import json
import os
import shutil

import chromadb
from sentence_transformers import SentenceTransformer

RULE_PATH = "data/rules.json"
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "governance_rules"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_rules(rule_path):
    with open(rule_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    if not isinstance(rules, list):
        raise ValueError("rules.json should be a list of rule objects.")

    required_keys = [
        "rule_id",
        "rule_name",
        "risk_type",
        "risk_level",
        "description",
        "evidence_keywords",
        "merchant_suggestion"
    ]

    for rule in rules:
        for key in required_keys:
            if key not in rule:
                raise ValueError(f"Missing key {key} in rule: {rule}")

    return rules


def rule_to_document(rule):
    keywords = ", ".join(rule.get("evidence_keywords", []))

    return f"""
Rule ID: {rule["rule_id"]}
Rule Name: {rule["rule_name"]}
Risk Type: {rule["risk_type"]}
Risk Level: {rule["risk_level"]}
Description: {rule["description"]}
Evidence Keywords: {keywords}
Merchant Suggestion: {rule["merchant_suggestion"]}
""".strip()


def build_knowledge_base():
    print("Loading rules...")
    rules = load_rules(RULE_PATH)
    print(f"Loaded {len(rules)} rules.")

    print("Loading embedding model...")
    print("This may take a few minutes the first time.")
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    # 为了避免重复建库导致数据混乱，每次重新生成 chroma_db
    if os.path.exists(CHROMA_PATH):
        print("Removing existing chroma_db...")
        shutil.rmtree(CHROMA_PATH)

    os.makedirs(CHROMA_PATH, exist_ok=True)

    print("Creating Chroma persistent client...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = client.create_collection(name=COLLECTION_NAME)

    documents = []
    metadatas = []
    ids = []

    for rule in rules:
        doc = rule_to_document(rule)

        documents.append(doc)
        metadatas.append({
            "rule_id": rule["rule_id"],
            "rule_name": rule["rule_name"],
            "risk_type": rule["risk_type"],
            "risk_level": rule["risk_level"]
        })
        ids.append(rule["rule_id"])

    print("Generating embeddings...")
    embeddings = embedder.encode(documents, show_progress_bar=True).tolist()

    print("Adding documents to Chroma...")
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print("Knowledge base built successfully.")
    print(f"Chroma path: {CHROMA_PATH}")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Total rules: {collection.count()}")

    return collection, embedder


def test_retrieval(collection, embedder):
    print("\nTesting retrieval...")

    test_queries = [
        "This face cream claims to remove wrinkles in 3 days and is 100% effective.",
        "This listing says the product is a replica luxury bag.",
        "This product title contains gun and ammo."
    ]

    for query in test_queries:
        print("\nQuery:")
        print(query)

        query_embedding = embedder.encode([query]).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )

        print("Top retrieved rules:")

        for meta, distance in zip(
            results["metadatas"][0],
            results["distances"][0]
        ):
            print(
                f"- {meta['rule_id']} | {meta['rule_name']} | "
                f"{meta['risk_type']} | distance={round(distance, 4)}"
            )


if __name__ == "__main__":
    collection, embedder = build_knowledge_base()
    test_retrieval(collection, embedder)