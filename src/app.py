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

# Display name to actual column mapping
metrics = {
    "Revenue": "Revenue",
    "Cost of Goods Sold (COGS)": "COGS",
    "Gross Profit": "Gross Profit",
    "Operating Expenses": "Operating Expenses",
    "Operating Income": "Operating Income",
    "Net Income": "Net Income"
}

# Create tabs using display names
tabs = st.tabs(list(metrics.keys()))

for i, (display_name, column_name) in enumerate(metrics.items()):
    with tabs[i]:
        if column_name not in filtered_df.columns:
            st.warning(f"No data available for {display_name}.")
            continue

        metric_data = filtered_df.dropna(subset=[column_name])

        if metric_data.empty:
            st.warning(f"No data available for {display_name} with selected filters.")
        else:
            fig = px.line(
                metric_data.sort_values("period"),
                x="period",
                y=column_name,
                markers=True,
                title=f"{display_name} over Time for {selected_company}",
                labels={"period": "Year", column_name: display_name}
            )
            fig.update_traces(mode="lines+markers", hovertemplate=f"%{{y:.2f}}")
            st.plotly_chart(fig, use_container_width=True)


# --- Comparison Chart ---
st.subheader("Compare with Another Company")

# Select another company for comparison (excluding the already selected one)
comparison_companies = [c for c in company_names if c != selected_company]
if comparison_companies:
    comparison_company = st.selectbox("Select Comparison Company", comparison_companies)
    # Filter df for comparison company and selected years
    df_comp = df[(df['company'] == comparison_company) & (df['period'].isin(selected_years))]
else:
    comparison_company = None
    df_comp = pd.DataFrame()

# Ensure metric display names are used and mapped to real column names
metric_display_names = list(metrics.keys())
comparison_metric_display = st.selectbox("Select Metric for Comparison", metric_display_names, index=0)
comparison_metric = metrics[comparison_metric_display]  # Get actual column name

# Check if the selected metric exists in the DataFrame
if df_comp.empty or comparison_metric not in df_comp.columns:
    st.warning(f"No data available for '{comparison_metric_display}' for comparison company.")
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
            title=f"{comparison_metric_display} Comparison with {comparison_company}",
            labels={"period": "Year", comparison_metric: comparison_metric_display}
        )
        fig2.update_traces(mode="lines+markers", hovertemplate="%{y:.2f}", line=dict(dash="dot"))
        st.plotly_chart(fig2, use_container_width=True)
