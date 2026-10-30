import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(df: pd.DataFrame, insights: str = "", chart_bytes: bytes = None) -> bytes:
    """Generates a downloadable PDF report summarizing the dataset and insights."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("AI Data Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Dataset Overview
    elements.append(Paragraph("1. Dataset Overview", styles["Heading2"]))
    overview_text = (
        f"<b>Total Rows:</b> {len(df):,}<br/>"
        f"<b>Total Columns:</b> {len(df.columns):,}<br/>"
        f"<b>Missing Values:</b> {int(df.isna().sum().sum()):,}<br/>"
        f"<b>Columns:</b> {', '.join(df.columns.tolist())}"
    )
    elements.append(Paragraph(overview_text, styles["Normal"]))
    elements.append(Spacer(1, 14))

    # Numeric Summary Table
    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        elements.append(Paragraph("2. Numeric Summary Statistics", styles["Heading2"]))
        desc_df = numeric_df.describe().round(2).reset_index()
        table_data = [desc_df.columns.tolist()] + desc_df.values.tolist()

        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9F9")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 14))

    # Insights Section
    if insights and insights.strip():
        elements.append(Paragraph("3. Key Insights & Observations", styles["Heading2"]))
        for line in insights.strip().split("\n"):
            if line.strip():
                elements.append(Paragraph(line.strip(), styles["Normal"]))
                elements.append(Spacer(1, 4))
        elements.append(Spacer(1, 12))

    # Chart Image (if provided)
    if chart_bytes:
        try:
            elements.append(Paragraph("4. Visual Chart", styles["Heading2"]))
            img_buffer = io.BytesIO(chart_bytes)
            img = Image(img_buffer, width=420, height=260)
            elements.append(img)
        except Exception:
            pass

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
