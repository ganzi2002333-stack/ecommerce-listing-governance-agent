import json
import time
import pandas as pd
import streamlit as st

from agent_graph import build_graph


st.set_page_config(
    page_title="E-commerce Listing Governance AI Agent",
    layout="wide"
)

st.title("E-commerce Listing Governance AI Agent")
st.caption("跨境电商商品治理 AI Agent Demo：商品输入 → 规则检索 → 风险判断 → 整改建议")


@st.cache_resource
def load_agent():
    return build_graph()


graph = load_agent()


with st.sidebar:
    st.header("Model Settings")
    model_name = st.selectbox(
        "Local LLM via Ollama",
        ["qwen2.5:3b"],
        index=0
    )

    st.markdown("---")
    st.write("当前 Demo 使用本地 Ollama + Qwen2.5:3b。")
    st.write("如果模型没有启动，请先确认 Ollama 正在运行。")


tab1, tab2 = st.tabs(["Single Listing Review", "Batch CSV Review"])


with tab1:
    st.subheader("Single Product Listing Review")

    col1, col2 = st.columns(2)

    with col1:
        product_id = st.text_input("Product ID", "demo_001")

        title = st.text_input(
            "Product Title",
            "Whitening Anti-aging Face Cream 100% Effective"
        )

        brand = st.text_input("Brand", "Unknown")

        category = st.text_input("Category", "Beauty")

    with col2:
        description = st.text_area(
            "Product Description",
            "Remove wrinkles in 3 days. Guaranteed result.",
            height=180
        )

    if st.button("Run Governance Agent", type="primary"):
        product = {
            "product_id": product_id,
            "title": title,
            "description": description,
            "brand": brand,
            "category": category
        }

        start_time = time.time()

        with st.spinner("Agent is reviewing the product listing..."):
            result = graph.invoke({
                "product": product,
                "model_name": model_name
            })

        elapsed = round(time.time() - start_time, 2)

        parsed_input = result.get("parsed_input", {})
        retrieved_rules = result.get("retrieved_rules", [])
        risk_result = result.get("risk_result", {})
        rewrite_result = result.get("rewrite_result", {})

        st.success(f"Review completed in {elapsed} seconds.")

        st.markdown("## 1. Risk Summary")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Risk Level",
            risk_result.get("risk_level", "N/A")
        )

        c2.metric(
            "Human Review Needed",
            str(risk_result.get("needs_human_review", "N/A"))
        )

        matched_rules = risk_result.get("matched_rule_ids", [])
        c3.metric(
            "Matched Rules",
            len(matched_rules) if isinstance(matched_rules, list) else "N/A"
        )

        st.markdown("## 2. Risk Judgement Result")
        st.json(risk_result)

        st.markdown("## 3. Merchant-facing Revision Suggestions")
        st.json(rewrite_result)

        st.markdown("## 4. Retrieved Governance Rules")

        for item in retrieved_rules:
            meta = item.get("metadata", {})
            rule_id = meta.get("rule_id", "")
            rule_name = meta.get("rule_name", "")
            risk_type = meta.get("risk_type", "")
            distance = item.get("distance", "")

            with st.expander(f"{rule_id} | {rule_name} | {risk_type}"):
                st.write(item.get("document", ""))
                st.write("Retrieval distance:", distance)

        st.markdown("## 5. Parsed Input")
        st.json(parsed_input)


with tab2:
    st.subheader("Batch CSV Review")

    st.write("上传 CSV 文件后，可以批量分析商品治理风险。")
    st.write("CSV 文件建议包含字段：product_id, title, description, brand, category")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    max_rows = st.number_input(
        "Max rows to process",
        min_value=1,
        max_value=50,
        value=5
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.markdown("### Uploaded Data Preview")
        st.dataframe(df.head())

        if st.button("Run Batch Review"):
            outputs = []
            review_df = df.head(max_rows).copy()

            progress = st.progress(0)

            for i, (_, row) in enumerate(review_df.iterrows()):
                product = {
                    "product_id": str(row.get("product_id", i + 1)),
                    "title": str(row.get("title", "")),
                    "description": str(row.get("description", "")),
                    "brand": str(row.get("brand", "")),
                    "category": str(row.get("category", ""))
                }

                start_time = time.time()

                try:
                    result = graph.invoke({
                        "product": product,
                        "model_name": model_name
                    })

                    risk_result = result.get("risk_result", {})
                    rewrite_result = result.get("rewrite_result", {})

                    risk_types = risk_result.get("risk_types", [])
                    matched_rule_ids = risk_result.get("matched_rule_ids", [])

                    outputs.append({
                        "product_id": product["product_id"],
                        "title": product["title"],
                        "risk_level": risk_result.get("risk_level", ""),
                        "risk_types": "; ".join(risk_types) if isinstance(risk_types, list) else "",
                        "matched_rule_ids": "; ".join(matched_rule_ids) if isinstance(matched_rule_ids, list) else "",
                        "needs_human_review": risk_result.get("needs_human_review", ""),
                        "explanation": risk_result.get("explanation", ""),
                        "merchant_message": rewrite_result.get("merchant_message", ""),
                        "rewritten_title": rewrite_result.get("rewritten_title", ""),
                        "elapsed_seconds": round(time.time() - start_time, 2)
                    })

                except Exception as e:
                    outputs.append({
                        "product_id": product["product_id"],
                        "title": product["title"],
                        "risk_level": "ERROR",
                        "error": str(e)
                    })

                progress.progress((i + 1) / len(review_df))

            out_df = pd.DataFrame(outputs)

            st.markdown("### Batch Review Results")
            st.dataframe(out_df)

            if "risk_level" in out_df.columns:
                st.markdown("### Risk Level Distribution")
                st.bar_chart(out_df["risk_level"].value_counts())

            csv = out_df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(
                label="Download Review Results CSV",
                data=csv,
                file_name="governance_agent_results.csv",
                mime="text/csv"
            )