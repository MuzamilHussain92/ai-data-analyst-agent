
import streamlit as st
import pandas as pd
import plotly.express as px

from dotenv import load_dotenv

from src.data_loader import load_data, detect_column_roles
from src.agent import build_agent, ask_agent
from src.report_generator import generate_pdf_report


# --------------------------------------------------
# 1. Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Data Analyst Agent",
    page_icon="📊",
    layout="wide",
)

load_dotenv()

st.title("📊 AI Data Analyst Agent")
st.caption(
    "Upload your dataset, ask questions in natural language, "
    "create charts, and generate analysis reports."
)


# --------------------------------------------------
# 2. Initialize session state
# --------------------------------------------------

if "data" not in st.session_state:
    st.session_state.data = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "loaded_file_name" not in st.session_state:
    st.session_state.loaded_file_name = None


# --------------------------------------------------
# 3. Sidebar: Upload dataset
# --------------------------------------------------

with st.sidebar:
    st.header("📁 Upload Dataset")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
    )

    if uploaded_file is not None:
        if (
            uploaded_file.name
            != st.session_state.loaded_file_name
        ):
            try:
                df_uploaded = load_data(uploaded_file)

                st.session_state.data = df_uploaded
                st.session_state.loaded_file_name = (
                    uploaded_file.name
                )

                # Reset the agent and chat for a new dataset
                st.session_state.agent = None
                st.session_state.chat_history = []

                st.success("Dataset uploaded successfully!")

            except Exception as exc:
                st.error(f"Could not load the dataset: {exc}")

    # Existing sidebar information: keep it
    if st.session_state.data is not None:
        sidebar_df = st.session_state.data

        st.divider()
        st.subheader("📋 Dataset Summary")

        st.write(
            f"**File:** {st.session_state.loaded_file_name}"
        )
        st.write(f"**Rows:** {len(sidebar_df):,}")
        st.write(f"**Columns:** {len(sidebar_df.columns)}")


# --------------------------------------------------
# 4. Stop if no dataset is uploaded
# --------------------------------------------------

if st.session_state.data is None:
    st.info(
        "Upload a CSV or Excel file using the sidebar "
        "to get started."
    )
    st.stop()


# IMPORTANT:
# Define df BEFORE using it in any section below.
df = st.session_state.data


# --------------------------------------------------
# 5. Dataset preview
# --------------------------------------------------

st.subheader("📄 Dataset Preview")

st.dataframe(
    df.head(10),
    use_container_width=True,
)

with st.expander("View all dataset rows"):
    st.dataframe(df, use_container_width=True)


# --------------------------------------------------
# 6. Automatically detected dataset information
# --------------------------------------------------

st.subheader("🔎 Dataset Understanding")

with st.expander("Detected Dataset Information", expanded=True):
    detected_roles = detect_column_roles(df)

    if detected_roles:
        st.write("**Recognized column roles:**")

        for role, column in detected_roles.items():
            st.write(f"- **{role}:** {column}")
    else:
        st.info(
            "No standard column roles were recognized. "
            "Your original columns are still available for analysis."
        )

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    date_columns = [
        column
        for column in df.columns
        if pd.api.types.is_datetime64_any_dtype(df[column])
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Numeric columns**")
        st.write(numeric_columns or "None detected")

    with col2:
        st.write("**Date columns**")
        st.write(date_columns or "None detected")


# --------------------------------------------------
# 7. Basic dataset statistics
# --------------------------------------------------

st.subheader("📈 Quick Statistics")

numeric_df = df.select_dtypes(include="number")

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.metric("Total Rows", f"{len(df):,}")

with metric2:
    st.metric("Total Columns", f"{len(df.columns):,}")

with metric3:
    st.metric(
        "Missing Values",
        f"{int(df.isna().sum().sum()):,}",
    )

if not numeric_df.empty:
    with st.expander("View numeric summary"):
        st.dataframe(
            numeric_df.describe().round(2),
            use_container_width=True,
        )


# --------------------------------------------------
# 8. AI Data Analyst Chat
# --------------------------------------------------

st.divider()
st.subheader("🤖 Ask Your AI Data Analyst")

st.write(
    "Ask questions about totals, categories, trends, "
    "top-performing records, and other dataset insights."
)

if st.session_state.agent is None:
    if st.button("Initialize AI Analyst", type="primary"):
        try:
            with st.spinner("Initializing AI Analyst..."):
                st.session_state.agent = build_agent(df)

            st.success("AI Analyst is ready!")

        except Exception as exc:
            st.error(
                f"Could not initialize the AI Analyst: {exc}"
            )

if st.session_state.agent is not None:

    # Display previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask a question about your dataset..."
    )

    if question:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your data..."):
                try:
                    answer = ask_agent(
                        st.session_state.agent,
                        question,
                        chat_history=st.session_state.chat_history[:-1],
                    )

                    st.markdown(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")


# --------------------------------------------------
# 9. Manual Chart Builder
# --------------------------------------------------

st.divider()
st.subheader("📊 Manual Chart Builder")

all_columns = df.columns.tolist()
numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()

if len(all_columns) > 0 and len(numeric_columns) > 0:

    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        category_column = st.selectbox(
            "Select category / X-axis",
            options=all_columns,
            key="chart_category",
        )

    with chart_col2:
        numeric_column = st.selectbox(
            "Select numeric measure / Y-axis",
            options=numeric_columns,
            key="chart_measure",
        )

    with chart_col3:
        chart_type = st.selectbox(
            "Select chart type",
            options=[
                "Bar Chart",
                "Line Chart",
                "Scatter Plot",
                "Pie Chart",
                "Histogram",
            ],
            key="chart_type",
        )

    try:
        if chart_type == "Bar Chart":
            chart_df = (
                df.groupby(category_column, dropna=False)[
                    numeric_column
                ]
                .sum()
                .reset_index()
            )

            fig = px.bar(
                chart_df,
                x=category_column,
                y=numeric_column,
                title=f"{numeric_column} by {category_column}",
            )

        elif chart_type == "Line Chart":
            chart_df = df.copy()

            if category_column != numeric_column:
                chart_df = chart_df.sort_values(
                    by=category_column
                )

            fig = px.line(
                chart_df,
                x=category_column,
                y=numeric_column,
                title=f"{numeric_column} by {category_column}",
                markers=True,
            )

        elif chart_type == "Scatter Plot":
            fig = px.scatter(
                df,
                x=category_column,
                y=numeric_column,
                title=f"{numeric_column} vs {category_column}",
            )

        elif chart_type == "Pie Chart":
            chart_df = (
                df.groupby(category_column, dropna=False)[
                    numeric_column
                ]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                chart_df,
                names=category_column,
                values=numeric_column,
                title=f"{numeric_column} by {category_column}",
            )

        else:
            fig = px.histogram(
                df,
                x=numeric_column,
                title=f"Distribution of {numeric_column}",
            )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    except Exception as exc:
        st.error(f"Could not create the chart: {exc}")

else:
    st.info(
        "Your dataset needs at least one numeric column "
        "to create charts."
    )


# --------------------------------------------------
# 10. Download processed dataset as CSV
# --------------------------------------------------

st.divider()
st.subheader("⬇️ Download Dataset")

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Dataset as CSV",
    data=csv_data,
    file_name="analyzed_dataset.csv",
    mime="text/csv",
)


# --------------------------------------------------
# 11. Generate PDF Analysis Report
# --------------------------------------------------

st.divider()
st.subheader("📄 Download Analysis Report")

report_insights = st.text_area(
    "Add AI findings or business observations to your report",
    placeholder=(
        "Paste useful findings from your AI chat here..."
    ),
    key="report_insights",
)

if st.button("Generate PDF Report", type="primary"):

    try:
        chart_bytes = None

        # Use the most recently created chart, if available.
        if "fig" in locals():
            try:
                chart_bytes = fig.to_image(format="png")
            except Exception:
                st.warning(
                    "The PDF will be generated without the chart image. "
                    "If chart export is required, check your Kaleido setup."
                )

        with st.spinner("Generating PDF report..."):
            pdf_bytes = generate_pdf_report(
                df=df,
                insights=report_insights,
                chart_bytes=chart_bytes,
            )

        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name="ai_data_analysis_report.pdf",
            mime="application/pdf",
            key="download_pdf_report",
        )

    except Exception as exc:
        st.error(f"Could not generate the report: {exc}")


# --------------------------------------------------
# 12. Footer
# --------------------------------------------------

st.divider()
st.caption("AI Data Analyst Agent | Powered by Python, Streamlit, and AI")
