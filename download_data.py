import os
import pandas as pd
from datasets import load_dataset

os.makedirs("data", exist_ok=True)

DATASET_NAME = "Shopify/product-catalogue"
OUTPUT_PATH = "data/products_sample.csv"
MAX_ROWS = 500


def get_first_available(row, candidates):
    for col in candidates:
        if col in row and row[col] is not None:
            value = row[col]
            if isinstance(value, str) and value.strip():
                return value.strip()
            if not isinstance(value, str):
                return str(value)
    return ""


def clean_text(value, max_len=1000):
    if value is None:
        return ""
    value = str(value)
    value = value.replace("\n", " ").replace("\r", " ")
    value = " ".join(value.split())
    return value[:max_len]


print("Loading dataset:", DATASET_NAME)

dataset_dict = load_dataset(DATASET_NAME, streaming=True)

if hasattr(dataset_dict, "keys"):
    split_name = list(dataset_dict.keys())[0]
    dataset = dataset_dict[split_name]
    print("Using split:", split_name)
else:
    dataset = dataset_dict

rows = []

for i, item in enumerate(dataset):
    if i == 0:
        print("Available columns:")
        print(list(item.keys()))

    title = get_first_available(
        item,
        ["title", "product_title", "name", "product_name"]
    )

    description = get_first_available(
        item,
        ["description", "body_html", "text", "product_description"]
    )

    brand = get_first_available(
        item,
        ["brand", "vendor", "manufacturer"]
    )

    category = get_first_available(
        item,
        ["category", "product_type", "taxonomy", "product_category"]
    )

    if not title:
        continue

    rows.append({
        "product_id": len(rows) + 1,
        "title": clean_text(title, 300),
        "description": clean_text(description, 1000),
        "brand": clean_text(brand, 100),
        "category": clean_text(category, 200)
    })

    if len(rows) >= MAX_ROWS:
        break

df = pd.DataFrame(rows)

df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("Saved:", OUTPUT_PATH)
print("Rows:", len(df))
print(df.head())