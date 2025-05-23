import streamlit as st
import pandas as pd
import plotly.express as px
import re

def sort_periods(periods):
    def extract_sort_key(p):
        match = re.search(r'(\d{4})', p)
        year = int(match.group(1)) if match else 0
        if p.startswith('Q'):
            quarter = int(re.search(r'Q(\d)', p).group(1))
            return (year, quarter)
        elif p.startswith('H'):
            half = int(re.search(r'H(\d)', p).group(1))
            return (year, half * 2)
        elif p.startswith('FY'):
            return (year, 0)
        elif p.isdigit():
            return (int(p), 1)
        else:
            return (year, 99)
    return sorted(periods, key=extract_sort_key)

@st.cache_data
def load_data():
    df = pd.read_csv("data\\financial_summaries\\financial_summary_all.csv")
    df.dropna(subset=["Revenue", "Net Income"], inplace=True)
    df.dropna(subset=['period'], inplace=True)
    df['period'] = df['period'].astype(str).str.strip()
    return df

df = load_data()

st.sidebar.title("Company Filter")

company_names = sorted(df['company'].dropna().unique())
selected_company = st.sidebar.selectbox("Select Company", company_names)

all_periods = sort_periods(df['period'].unique())
selected_years = st.sidebar.multiselect("Select Periods", all_periods, default=all_periods)

filtered_df = df[(df['company'] == selected_company) & (df['period'].isin(selected_years))]
metrics = {
    "Revenue": "Revenue",
    "Cost of Goods Sold (COGS)": "COGS",
    "Gross Profit": "Gross Profit",
    "Operating Expenses": "Operating Expenses",
    "Operating Income": "Operating Income",
    "Net Income": "Net Income"
}

# --- Tabs for each metric ---
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
            metric_data['period'] = pd.Categorical(metric_data['period'], categories=all_periods, ordered=True)
            metric_data.sort_values("period", inplace=True)

            fig = px.line(
                metric_data,
                x="period",
                y=column_name,
                markers=True,
                title=f"{display_name} Over Time for {selected_company}",
                labels={"period": "Period", column_name: display_name}
            )
            fig.update_traces(mode="lines+markers", hovertemplate="%{y:.2f}")
            st.plotly_chart(fig, use_container_width=True)

# --- Comparison Chart ---
st.subheader("Compare with Another Company")

comparison_companies = [c for c in company_names if c != selected_company]
if comparison_companies:
    comparison_company = st.selectbox("Select Comparison Company", comparison_companies)
    df_comp = df[(df['company'] == comparison_company) & (df['period'].isin(selected_years))]
else:
    comparison_company = None
    df_comp = pd.DataFrame()

metric_display_names = list(metrics.keys())
comparison_metric_display = st.selectbox("Select Metric for Comparison", metric_display_names, index=0)
comparison_metric = metrics[comparison_metric_display]

if df_comp.empty or comparison_metric not in df_comp.columns:
    st.warning(f"No data available for '{comparison_metric_display}' for comparison company.")
else:
    primary_data = filtered_df[[comparison_metric, 'period']].copy()
    primary_data['Company'] = selected_company

    secondary_data = df_comp[[comparison_metric, 'period']].copy()
    secondary_data['Company'] = comparison_company

    combined_data = pd.concat([primary_data, secondary_data])
    combined_data.dropna(subset=[comparison_metric], inplace=True)
    combined_data['period'] = pd.Categorical(combined_data['period'], categories=all_periods, ordered=True)
    combined_data.sort_values("period", inplace=True)

    if combined_data.empty:
        st.warning("No comparison data available for selected metric and periods.")
    else:
        fig2 = px.line(
            combined_data,
            x="period",
            y=comparison_metric,
            color="Company",
            markers=True,
            title=f"{comparison_metric_display} Comparison: {selected_company} vs {comparison_company}",
            labels={"period": "Period", comparison_metric: comparison_metric_display, "Company": "Company"}
        )
        fig2.update_traces(mode="lines+markers", hovertemplate="%{y:.2f}")
        st.plotly_chart(fig2, use_container_width=True)