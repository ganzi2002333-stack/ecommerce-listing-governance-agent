import time
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from agent_graph import build_graph

MODEL_NAME = "qwen2.5:3b"
EVAL_PATH = "data/risky_test_cases.csv"
OUTPUT_PATH = "data/eval_risky_results.csv"

graph = build_graph()

df = pd.read_csv(EVAL_PATH)

df["manual_risk_level"] = df["manual_risk_level"].astype(str).str.strip()
df = df[df["manual_risk_level"].isin(["High", "Medium", "Low"])]

if len(df) == 0:
    raise ValueError("No valid labels found. manual_risk_level must be High, Medium, or Low.")

results = []

for idx, row in df.iterrows():
    product = {
        "product_id": str(row.get("product_id", idx)),
        "title": str(row.get("title", "")),
        "description": str(row.get("description", "")),
        "brand": str(row.get("brand", "")),
        "category": str(row.get("category", ""))
    }

    start_time = time.time()

    try:
        result = graph.invoke({
            "product": product,
            "model_name": MODEL_NAME
        })

        risk_result = result.get("risk_result", {})
        rewrite_result = result.get("rewrite_result", {})

        agent_risk_level = risk_result.get("risk_level", "Unknown")
        risk_types = risk_result.get("risk_types", [])
        matched_rule_ids = risk_result.get("matched_rule_ids", [])

        is_correct = row["manual_risk_level"] == agent_risk_level

        results.append({
            "product_id": product["product_id"],
            "title": product["title"],
            "description": product["description"],
            "manual_risk_level": row["manual_risk_level"],
            "agent_risk_level": agent_risk_level,
            "is_correct": is_correct,
            "manual_risk_types": row.get("manual_risk_types", ""),
            "agent_risk_types": "; ".join(risk_types) if isinstance(risk_types, list) else "",
            "manual_rule_ids": row.get("matched_rule_ids", ""),
            "agent_rule_ids": "; ".join(matched_rule_ids) if isinstance(matched_rule_ids, list) else "",
            "needs_human_review": risk_result.get("needs_human_review", ""),
            "explanation": risk_result.get("explanation", ""),
            "merchant_message": rewrite_result.get("merchant_message", ""),
            "elapsed_seconds": round(time.time() - start_time, 2)
        })

        print(
            f"Done {len(results)}/{len(df)} | "
            f"product_id={product['product_id']} | "
            f"manual={row['manual_risk_level']} | "
            f"agent={agent_risk_level} | "
            f"correct={is_correct}"
        )

    except Exception as e:
        results.append({
            "product_id": product["product_id"],
            "title": product["title"],
            "manual_risk_level": row["manual_risk_level"],
            "agent_risk_level": "ERROR",
            "is_correct": False,
            "error": str(e)
        })

out_df = pd.DataFrame(results)
out_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

valid_df = out_df[out_df["agent_risk_level"].isin(["High", "Medium", "Low"])]

print("\nSaved:", OUTPUT_PATH)
print("Total evaluated rows:", len(valid_df))

if len(valid_df) > 0:
    accuracy = accuracy_score(
        valid_df["manual_risk_level"],
        valid_df["agent_risk_level"]
    )

    print("\nAccuracy:")
    print(round(accuracy, 4))

    print("\nClassification Report:")
    print(classification_report(
        valid_df["manual_risk_level"],
        valid_df["agent_risk_level"],
        labels=["High", "Medium", "Low"],
        zero_division=0
    ))

    print("\nConfusion Matrix:")
    print(confusion_matrix(
        valid_df["manual_risk_level"],
        valid_df["agent_risk_level"],
        labels=["High", "Medium", "Low"]
    ))

    print("\nAverage response time:")
    print(round(valid_df["elapsed_seconds"].mean(), 2), "seconds")

    print("\nIncorrect cases:")
    wrong_df = valid_df[valid_df["is_correct"] == False]
    if len(wrong_df) == 0:
        print("No incorrect cases.")
    else:
        print(wrong_df[[
            "product_id",
            "title",
            "manual_risk_level",
            "agent_risk_level",
            "manual_risk_types",
            "agent_risk_types",
            "explanation"
        ]])