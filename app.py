import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. SETUP & CONFIG
st.set_page_config(page_title="Warehouse Performance Analyzer", layout="wide")

# 2. DATA ENGINE (The "Single Source of Truth")
@st.cache_resource
def get_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, date_cols

df_raw, chronological_months = get_data()

# 3. SIDEBAR (Defined globally so it never disappears)
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"])
capacity_range = st.sidebar.slider("Capacity Boundary (MT)", 0, 50000, (0, 20000))

# 4. TABS (The Navigation Skeleton)
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY (The Performance Matrix)
with tabs[0]:
    st.subheader(f"Portfolio Financial Overview - {selected_fy}")
    # Logic: Filter df_raw by selected_fy and capacity_range
    st.write("Summary logic ready. Use df_raw and selected_fy to populate your Metrics rows.")

# TAB 1: YoY RENT ANALYZER
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Analyzer")
    st.write("Seasoned asset filter and PSF bar charts will display here.")

# TAB 2: COMPARE YEARS
with tabs[2]:
    st.subheader("Compare Two Years")
    c1, c2 = st.columns(2)
    yr1 = c1.selectbox("Baseline Year", ["FY 23-24", "FY 24-25", "FY 25-26"], key="b")
    yr2 = c2.selectbox("Target Year", ["FY 23-24", "FY 24-25", "FY 25-26"], key="t")
    st.write("Overlay charts and matrix ledger will display here.")

# TAB 3: WAREHOUSE DRILLDOWN
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
    else:
        st.warning("No data found for this asset.")
