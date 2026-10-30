import os
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def build_agent(df: pd.DataFrame) -> dict:
    """Initializes the Groq LLM and prepares dataset context for analysis."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Set it in your .env file or Streamlit Secrets.")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.1,
    )

    # Pre-compute rich dataset summary so the LLM can answer accurately
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    cat_summary = []
    for col in categorical_cols[:10]:
        if df[col].nunique() <= 25:
            top_vals = df[col].value_counts().head(10).to_dict()
            cat_summary.append(f"- {col} (top counts): {top_vals}")
            if numeric_cols:
                grouped = df.groupby(col)[numeric_cols].sum().round(2).to_dict()
                cat_summary.append(f"  {col} totals: {grouped}")

    context = f"""Dataset Shape: {len(df)} rows, {len(df.columns)} columns
Columns & Types: {df.dtypes.astype(str).to_dict()}

Numeric Summary Statistics:
{df.describe().round(2).to_string() if numeric_cols else "No numeric columns"}

Numeric Column Totals (Sums):
{df[numeric_cols].sum().round(2).to_dict() if numeric_cols else "None"}

Categorical Breakdowns & Aggregations:
{chr(10).join(cat_summary)}

Sample Rows (First 10):
{df.head(10).to_string()}
"""

    return {"llm": llm, "context": context}

def ask_agent(agent: dict, question: str, chat_history: list = None) -> str:
    """Sends the user question and dataset context to the Groq LLM."""
    llm = agent["llm"]
    context = agent["context"]

    system_prompt = (
        "You are an expert AI Data Analyst. Answer the user's question clearly, "
        "accurately, and concisely using ONLY the dataset statistics and aggregations "
        "provided below. Format key numbers with commas/decimals and use bullet points "
        "or markdown tables when helpful.\n\n"
        f"{context}"
    )

    messages = [SystemMessage(content=system_prompt)]
    if chat_history:
        for msg in chat_history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=question))
    response = llm.invoke(messages)
    return response.content
