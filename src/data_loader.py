import pandas as pd

def load_data(uploaded_file) -> pd.DataFrame:
    """Loads a CSV or Excel file into a pandas DataFrame."""
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

    # Attempt to parse date-like columns automatically
    for col in df.columns:
        if df[col].dtype == "object" and any(k in col.lower() for k in ["date", "time", "day", "month", "year"]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass
    return df

def detect_column_roles(df: pd.DataFrame) -> dict:
    """Detects common business column roles based on column names."""
    roles = {}
    role_keywords = {
        "ID / Identifier": ["id", "receipt", "order", "invoice", "code"],
        "Date / Time": ["date", "time", "timestamp", "day", "month", "year"],
        "Location / Geography": ["city", "state", "region", "country", "store", "branch", "location"],
        "Category / Segment": ["category", "sub-category", "segment", "type", "department", "group"],
        "Revenue / Sales": ["sales", "revenue", "amount", "total", "price"],
        "Profit / Margin": ["profit", "margin", "earnings", "net"],
        "Quantity / Volume": ["quantity", "qty", "count", "units"],
        "Discount": ["discount", "promo", "rebate"],
        "Payment Method": ["payment", "method", "channel"],
    }

    for role, keywords in role_keywords.items():
        matched_cols = [
            col for col in df.columns
            if any(k in col.lower() for k in keywords)
        ]
        if matched_cols:
            roles[role] = ", ".join(matched_cols)

    return roles
