import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/financial_summaries/combined_financial_summary.csv")
    df.dropna(subset=["Revenue", "Net Income"], inplace=True)
    # Ensure 'period' is integer and clean
    df['period'] = pd.to_numeric(df['period'], errors='coerce')
    df.dropna(subset=['period'], inplace=True)
    df['period'] = df['period'].astype(int)
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("Company Filter")

# Use 'company' column, unique sorted list for selection
company_names = sorted(df['company'].dropna().unique())
selected_company = st.sidebar.selectbox("Select Company", company_names)

# Global period selector (all periods in data)
all_periods = sorted(df['period'].unique())
selected_years = st.sidebar.multiselect("Select Years", all_periods, default=all_periods)

# Filter by company and selected years (for all tabs)
filtered_df = df[(df['company'] == selected_company) & (df['period'].isin(selected_years))]

# Metrics for tabs
metrics = [
    "Revenue",
    "Cost of Goods Sold (COGS)",
    "Gross Profit",
    "Operating Expenses",
    "Operating Income",
    "Net Income"
]

st.title(f"Financial Metrics Trend for {selected_company}")

# Create tabs for each metric
tabs = st.tabs(metrics)

for i, metric in enumerate(metrics):
    with tabs[i]:
        metric_col = metric  # column names should match exactly as in your dataframe
        if metric_col not in filtered_df.columns:
            st.warning(f"No data available for {metric}.")
            continue

        metric_data = filtered_df.dropna(subset=[metric_col])

        if metric_data.empty:
            st.warning(f"No data available for {metric} with selected filters.")
        else:
            fig = px.line(
                metric_data.sort_values("period"),
                x="period",
                y=metric_col,
                markers=True,
                title=f"{metric} over Time for {selected_company}",
                labels={"period": "Year", metric_col: metric}
            )
            fig.update_traces(mode="lines+markers", hovertemplate=f"%{{y:.2f}}")
            st.plotly_chart(fig, use_container_width=True)

# --- Comparison Chart ---
st.subheader("Compare with Another Company")

comparison_company = st.selectbox(
    "Select Company for Comparison",
    [c for c in company_names if c != selected_company]
)

df_comp = df[(df['company'] == comparison_company) & (df['period'].isin(selected_years))]

# Comparison metric selection for consistency with main tabs
comparison_metric = st.selectbox("Select Metric for Comparison", metrics, index=metrics.index("Revenue"))

if comparison_metric not in df_comp.columns:
    st.warning(f"No data available for {comparison_metric} for comparison company.")
else:
    comp_data = df_comp.dropna(subset=[comparison_metric])

    if comp_data.empty:
        st.warning("No data available for comparison company and selected years.")
    else:
        fig2 = px.line(
            comp_data.sort_values("period"),
            x="period",
            y=comparison_metric,
            markers=True,
            title=f"{comparison_metric} Comparison with {comparison_company}",
            labels={"period": "Year", comparison_metric: comparison_metric}
        )
        fig2.update_traces(mode="lines+markers", hovertemplate=f"%{{y:.2f}}", line=dict(dash="dot"))
        st.plotly_chart(fig2, use_container_width=True)
