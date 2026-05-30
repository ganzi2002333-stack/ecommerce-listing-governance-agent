import json
import re
from typing import TypedDict, Dict, Any, List

import requests
import chromadb
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, START, END


CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "governance_rules"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MODEL = "qwen2.5:3b"


embedder = SentenceTransformer(EMBEDDING_MODEL)
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(COLLECTION_NAME)


class AgentState(TypedDict, total=False):
    product: Dict[str, Any]
    parsed_input: Dict[str, Any]
    retrieved_rules: List[Dict[str, Any]]
    risk_result: Dict[str, Any]
    rewrite_result: Dict[str, Any]
    model_name: str


def call_ollama(prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Call local Ollama model.
    Make sure Ollama is installed and qwen2.5:3b has been pulled.
    """
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Please make sure Ollama is installed and running."
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP error: {e}")
    except Exception as e:
        raise RuntimeError(f"Ollama call failed: {e}")


def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from model output.
    The model may return pure JSON or JSON wrapped in markdown.
    """
    if not text:
        return {
            "parse_error": True,
            "raw_output": text
        }

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Remove markdown code block markers if they exist
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # Last attempt: extract content between first { and last }
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {
        "parse_error": True,
        "raw_output": text
    }


def node_parse_input(state: AgentState) -> AgentState:
    """
    Node 1: Parse product input and identify simple risk cues.
    """
    product = state["product"]

    title = str(product.get("title", ""))
    description = str(product.get("description", ""))
    brand = str(product.get("brand", ""))
    category = str(product.get("category", ""))

    full_text = f"""
Title: {title}
Description: {description}
Brand: {brand}
Category: {category}
""".strip()

    simple_cues = []

    risky_words = [
        "100%",
        "guaranteed",
        "cure",
        "treat",
        "remove wrinkles",
        "replica",
        "fake",
        "gun",
        "knife",
        "prescription",
        "FDA approved",
        "limited stock",
        "best seller",
        "instant",
        "no.1",
        "luxury",
        "copy"
    ]

    lower_text = full_text.lower()

    for word in risky_words:
        if word.lower() in lower_text:
            simple_cues.append(word)

    return {
        "parsed_input": {
            "full_text": full_text,
            "simple_cues": simple_cues,
            "query": full_text
        }
    }


def node_retrieve_rules(state: AgentState) -> AgentState:
    """
    Node 2: Retrieve relevant governance rules from Chroma.
    """
    query = state["parsed_input"]["query"]

    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "document": doc,
            "metadata": meta,
            "distance": dist
        })

    return {
        "retrieved_rules": retrieved
    }


def node_risk_judgement(state: AgentState) -> AgentState:
    """
    Node 3: Use LLM to judge listing risk based on retrieved rules.
    """
    product = state["product"]
    parsed_input = state["parsed_input"]
    retrieved_rules = state["retrieved_rules"]
    model_name = state.get("model_name", DEFAULT_MODEL)

    rules_text = "\n\n".join([
        item["document"] for item in retrieved_rules
    ])

    prompt = f"""
You are an e-commerce listing governance AI assistant.

Your task:
Assess the product listing risk ONLY based on the given governance rules.
Do not invent internal platform policies.
Return JSON only. Do not use markdown.

Product:
{json.dumps(product, ensure_ascii=False, indent=2)}

Detected simple cues:
{json.dumps(parsed_input.get("simple_cues", []), ensure_ascii=False)}

Retrieved governance rules:
{rules_text}

Return JSON with this exact schema:
{{
  "risk_level": "High/Medium/Low",
  "risk_types": ["type1", "type2"],
  "matched_rule_ids": ["R001"],
  "evidence": ["short evidence from product text"],
  "explanation": "short explanation",
  "needs_human_review": true
}}

Risk level rules:
- High: prohibited, restricted, medical, weapon, counterfeit, privacy, dangerous product
- Medium: misleading claim, exaggerated claim, category mismatch, keyword stuffing, unverified certification
- Low: incomplete information, unclear brand, poor readability
"""

    output = call_ollama(prompt, model_name=model_name)
    risk_result = extract_json(output)

    return {
        "risk_result": risk_result
    }


def node_rewrite_suggestion(state: AgentState) -> AgentState:
    """
    Node 4: Generate merchant-facing revision suggestions.
    """
    product = state["product"]
    risk_result = state["risk_result"]
    retrieved_rules = state["retrieved_rules"]
    model_name = state.get("model_name", DEFAULT_MODEL)

    rules_summary = [
        item["metadata"] for item in retrieved_rules
    ]

    prompt = f"""
You are an e-commerce merchant service assistant.

Your task:
Based on the product listing and risk result, generate practical revision suggestions for the merchant.
Return JSON only. Do not use markdown.

Product:
{json.dumps(product, ensure_ascii=False, indent=2)}

Risk result:
{json.dumps(risk_result, ensure_ascii=False, indent=2)}

Matched rules summary:
{json.dumps(rules_summary, ensure_ascii=False, indent=2)}

Return JSON with this exact schema:
{{
  "merchant_message": "friendly explanation to merchant",
  "action_items": ["action 1", "action 2"],
  "rewritten_title": "safer title suggestion",
  "rewritten_description": "safer description suggestion"
}}
"""

    output = call_ollama(prompt, model_name=model_name)
    rewrite_result = extract_json(output)

    return {
        "rewrite_result": rewrite_result
    }


def build_graph():
    """
    Build LangGraph workflow.
    """
    graph = StateGraph(AgentState)

    graph.add_node("parse_input", node_parse_input)
    graph.add_node("retrieve_rules", node_retrieve_rules)
    graph.add_node("risk_judgement", node_risk_judgement)
    graph.add_node("rewrite_suggestion", node_rewrite_suggestion)

    graph.add_edge(START, "parse_input")
    graph.add_edge("parse_input", "retrieve_rules")
    graph.add_edge("retrieve_rules", "risk_judgement")
    graph.add_edge("risk_judgement", "rewrite_suggestion")
    graph.add_edge("rewrite_suggestion", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    sample_product = {
        "product_id": "demo_001",
        "title": "Whitening Anti-aging Face Cream 100% Effective",
        "description": "Remove wrinkles in 3 days. Guaranteed result.",
        "brand": "Unknown",
        "category": "Beauty"
    }

    result = app.invoke({
        "product": sample_product,
        "model_name": DEFAULT_MODEL
    })

    print(json.dumps(result, ensure_ascii=False, indent=2))