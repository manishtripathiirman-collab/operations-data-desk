import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. CONFIG & DATA PROCESSING
# ---------------------------------------------------------
st.set_page_config(page_title="Warehouse Performance Analyzer", layout="wide")

@st.cache_resource
def load_and_process():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Logical FY Grouping
    fy_map = {
        "FY 23-24": [c for c in date_cols if c <= "2024-03-01"],
        "FY 24-25": [c for c in date_cols if c >= "2024-04-01" and c <= "2025-03-01"],
        "FY 25-26": [c for c in date_cols if c >= "2025-04-01"]
    }
    return df, date_cols, fy_map

df_raw, chron_months, fy_map = load_and_process()

# Data Transformation Engine
def get_metrics(fy):
    cols = fy_map[fy]
    df = df_raw.copy()
    df['Rev'] = df[df["Type_Clean"].str.contains("rev", na=False)][cols].sum(axis=1)
    df['Rent'] = df[df["Type_Clean"].str.contains("rent", na=False)][cols].sum(axis=1)
    df['Cap'] = df[df["Type_Clean"].str.contains("cap", na=False)][cols].mean(axis=1)
    return df.groupby('CMP ID').agg({'Rev':'sum', 'Rent':'sum', 'Cap':'mean', 'Cluster': 'first'}).reset_index()

# ---------------------------------------------------------
# 1. SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Select Fiscal Year", list(fy_map.keys()))

# ---------------------------------------------------------
# 2. TABS
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Two Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader(f"Portfolio Summary - {selected_fy}")
    data = get_metrics(selected_fy)
    
    # UI Metric Display (Row 1 & 2)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", f"₹{data['Rev'].sum():,.0f}")
    c2.metric("Rent", f"₹{data['Rent'].sum():,.0f}")
    c3.metric("Net Surplus", f"₹{(data['Rev']-data['Rent']).sum():,.0f}")
    c4.metric("Efficiency", f"{((data['Rent'].sum()/data['Rev'].sum())*100):.1f}%")

    c_a, c_b, c_c = st.columns(3)
    c_a.metric("Area Leased (SqFt)", f"{data['Cap'].sum()*6:,.0f}")
    c_b.metric("Rev / Sq. Ft.", f"₹{(data['Rev'].sum()/(data['Cap'].sum()*6)):,.2f}")
    c_c.metric("Rent / Sq. Ft.", f"₹{(data['Rent'].sum()/(data['Cap'].sum()*6)):,.2f}")

    # Viz
    col1, col2 = st.columns(2)
    with col1:
        st.write("Top 10 Clusters by Revenue")
        st.bar_chart(data.groupby('Cluster')['Rev'].sum().sort_values().tail(10))

# TAB 3: DRILLDOWN (Kept working as requested)
with tabs[3]:
    target_wh = st.selectbox("Facility:", options=sorted(df_raw["CMP ID"].unique()))
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    
    rev = wh_slice[wh_slice["Type_Clean"].str.contains("rev", na=False)]
    rent = wh_slice[wh_slice["Type_Clean"].str.contains("rent", na=False)]
    
    if not rev.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chron_months, y=rev[chron_months].values.flatten(), name="Rev"))
        fig.add_trace(go.Scatter(x=chron_months, y=rent[chron_months].values.flatten(), name="Rent"))
        st.plotly_chart(fig, use_container_width=True)
