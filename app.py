import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Warehouse Analytics Pro", layout="wide")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data (CSV/Excel)", type=["csv", "xlsx"])

if not uploaded_file:
    st.info("Please upload your 'Warehouse_Analysis_Wide_Format.xlsx' file in the sidebar to begin.")
    st.stop()

@st.cache_data
def process_data(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    # Assuming 'Details' column contains keywords like 'Rev', 'Rent', 'Cap'
    df['Type_Clean'] = df['Details'].astype(str).str.lower()
    return df

df_raw = process_data(uploaded_file)
tabs = st.tabs(["📈 Portfolio Performance", "🔄 YoY Rent Analyzer", "📊 Compare Two Years", "🔍 Individual Drilldown"])

# TAB 1: Portfolio Summary
with tabs[0]:
    st.subheader("Portfolio Financial Summary")
    # Calculation Logic: Use grouped sums based on Type_Clean
    metrics = df_raw.groupby('Type_Clean').sum(numeric_only=True).sum(axis=1)
    rev = metrics.get('rev', 0)
    rent = metrics.get('rent', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{rev:,.0f}")
    col2.metric("Total Rent", f"₹{rent:,.0f}")
    col3.metric("Net Surplus", f"₹{rev-rent:,.0f}")
    col4.metric("Efficiency", f"{((rent/rev)*100):.1f}%")

# TAB 2: YoY Rent Analyzer
with tabs[2]:
    st.subheader("Compare Two Years")
    c1, c2 = st.columns(2)
    yr1 = c1.selectbox("Baseline Year", ["2023", "2024", "2025"])
    yr2 = c2.selectbox("Target Year", ["2024", "2025", "2026"])
    
    # Overlay Chart Logic
    fig = go.Figure()
    fig.add_trace(go.Bar(name=yr1, x=df_raw['CMP ID'], y=df_raw.filter(like=yr1).sum(axis=1)))
    fig.add_trace(go.Bar(name=yr2, x=df_raw['CMP ID'], y=df_raw.filter(like=yr2).sum(axis=1)))
    fig.update_layout(barmode='overlay')
    st.plotly_chart(fig, use_container_width=True)

# TAB 4: Individual Drilldown
with tabs[3]:
    target = st.selectbox("Select Warehouse:", df_raw['CMP ID'].unique())
    data = df_raw[df_raw['CMP ID'] == target]
    st.line_chart(data.filter(like="202"))
