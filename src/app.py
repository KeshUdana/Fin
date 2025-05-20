import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data\\financial_summaries\\combined_financial_summary.csv")
    df.dropna(subset=["Revenue", "Net Income"], inplace=True)
    return df

df = load_data()

# Sidebar filters
st.sidebar.title("Company Filter")
company_files = df['filename'].dropna().unique()
selected_company = st.sidebar.selectbox("Select Company", company_files)

available_metrics = ["Revenue", "COGS", "Gross Profit", "Operating Income", "Net Income"]
selected_metric = st.sidebar.selectbox("Select Metric", available_metrics)

# Filter by selected company
filtered_df = df[df['filename'] == selected_company]

# Time period selector
years = filtered_df['period'].dropna().astype(int).unique()
selected_years = st.sidebar.multiselect("Select Years", sorted(years), default=sorted(years))

filtered_df = filtered_df[filtered_df['period'].isin(selected_years)]

# Main chart
st.title(f"{selected_metric} Trend for {selected_company}")

fig = px.line(filtered_df.sort_values("period"),
              x="period",
              y=selected_metric,
              markers=True,
              title=f"{selected_metric} over Time",
              labels={"period": "Year", selected_metric: selected_metric})

fig.update_traces(mode="lines+markers", hovertemplate=f"%{{y:.2f}}")

st.plotly_chart(fig, use_container_width=True)

# --- Comparison Chart ---
st.subheader("Compare with Another Company")

comparison_company = st.selectbox("Select Company for Comparison", [c for c in company_files if c != selected_company])

df_comp = df[df['filename'] == comparison_company]
df_comp = df_comp[df_comp['period'].isin(selected_years)]

fig2 = px.line(df_comp.sort_values("period"),
               x="period",
               y=selected_metric,
               markers=True,
               title=f"{selected_metric} Comparison with {comparison_company}",
               labels={"period": "Year", selected_metric: selected_metric})

fig2.update_traces(mode="lines+markers", hovertemplate=f"%{{y:.2f}}", line=dict(dash="dot"))

st.plotly_chart(fig2, use_container_width=True)

