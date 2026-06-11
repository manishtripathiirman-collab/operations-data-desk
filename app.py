import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. CONFIG & DATA LOAD
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
    
    # Fiscal Year Mapping
    fy_map = {
        "FY 23-24": [c for c in date_cols if c >= "2023-04-01" and c <= "2024-03-01"],
        "FY 24-25": [c for c in date_cols if c >= "2024-04-01" and c <= "2025-03-01"],
        "FY 25-26": [c for c in date_cols if c >= "2025-04-01" and c <= "2026-03-01"]
    }
    return df, date_cols, fy_map

df_raw, chronological_months, fy_map = load_and_process()

# Data Builder Function used by all Tabs
def get_fy_data(fy):
    cols = fy_map[fy]
    subset = df_raw.copy()
    subset['Rev'] = subset[subset["Type_Clean"].str.contains("rev", na=False)][cols].sum(axis=1)
    subset['Rent'] = subset[subset["Type_Clean"].str.contains("rent", na=False)][cols].sum(axis=1)
    subset['Cap'] = subset[subset["Type_Clean"].str.contains("cap", na=False)][cols].mean(axis=1)
    return subset.groupby('CMP ID').agg({'Rev':'sum', 'Rent':'sum', 'Cap':'mean'}).reset_index()

# ---------------------------------------------------------
# 1. SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", list(fy_map.keys()))
capacity_range = st.sidebar.slider("Capacity Boundary", 0, 50000, (0, 20000))

# ---------------------------------------------------------
# 2. TABS
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader(f"Portfolio Summary - {selected_fy}")
    data = get_fy_data(selected_fy)
    st.metric("Total Revenue", f"₹{data['Rev'].sum():,.0f}")
    st.dataframe(data)

# TAB 1: YoY RENT
with tabs[1]:
    st.subheader("YoY Rent Analyzer")
    st.write("Analysis logic can be built here using get_fy_data for all years.")

# TAB 2: COMPARE
with tabs[2]:
    st.subheader("Year-over-Year Comparison")
    c1, c2 = st.columns(2)
    y1 = c1.selectbox("Baseline Year", list(fy_map.keys()))
    y2 = c2.selectbox("Target Year", list(fy_map.keys()))
    st.write("Comparative analysis logic goes here.")

# TAB 3: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target_wh = st.selectbox("Select Facility:", options=sorted(df_raw["CMP ID"].unique()))
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    
    rev_row = wh_slice[wh_slice["Type_Clean"].str.contains("rev", na=False)]
    rent_row = wh_slice[wh_slice["Type_Clean"].str.contains("rent", na=False)]
    
    if not rev_row.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chronological_months, y=rev_row[chronological_months].values.flatten(), name="Revenue"))
        fig.add_trace(go.Scatter(x=chronological_months, y=rent_row[chronological_months].values.flatten(), name="Rent"))
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
