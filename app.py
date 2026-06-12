import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Warehouse Dashboard")

# 1. LOAD DATA
@st.cache_data
def load_data():
    # Load the cleaned CSV directly
    df = pd.read_csv('Warehouse_Analysis_Cleaned.csv')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

df = load_data()

# 2. APP LAYOUT
st.title("📦 Warehouse Performance Dashboard")

# 3. TABS
tabs = st.tabs(["📈 Portfolio Overview", "🔍 Site Drilldown"])

# TAB 1: PORTFOLIO
with tabs[0]:
    st.subheader("Portfolio Summary")
    # Grouping by metric to show high-level totals
    pivot = df.groupby('Metric')['Value'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"₹{pivot.get('Rev', 0):,.0f}")
    c2.metric("Total Rent", f"₹{pivot.get('Rent', 0):,.0f}")
    c3.metric("Total Capacity", f"{pivot.get('Cap', 0):,.0f} MT")

# TAB 2: DRILLDOWN
with tabs[1]:
    st.subheader("Site-Specific Trends")
    target = st.selectbox("Choose a Site:", df['Warehouse'].unique())
    site_df = df[df['Warehouse'] == target]
    
    # Create charts for each metric
    for m in ['Rev', 'Rent', 'Cap']:
        fig = px.line(
            site_df[site_df['Metric'] == m], 
            x='Date', y='Value', 
            title=f"{m} Trend for {target}", 
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
