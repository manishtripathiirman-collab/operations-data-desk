import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. CONFIG & DATA LOAD
# ---------------------------------------------------------
st.set_page_config(page_title="Warehouse Performance & Dehire Analyzer", layout="wide")

@st.cache_resource
def load_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Map to FY groups
    fy_map = {
        "FY 23-24": [c for c in date_cols if "2023" in c or "2024-01" in c or "2024-02" in c or "2024-03" in c],
        "FY 24-25": [c for c in date_cols if any(m in c for m in ["2024-04", "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12", "2025-01", "2025-02", "2025-03"])],
        "FY 25-26": [c for c in date_cols if any(m in c for m in ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"])]
    }
    return df, date_cols, fy_map

df_raw, chronological_months, fy_map = load_data()

# Sidebar controls
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year Focus", list(fy_map.keys()))

# ---------------------------------------------------------
# 1. TABS SETUP
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Two Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader(f"Portfolio Summary - {selected_fy}")
    # Placeholder for logic: Summing Rev, Rent, Net Surplus using fy_map[selected_fy]
    st.write("Financial totals and capacity metrics rendering here...")

# TAB 1: YoY RENT ANALYZER
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Analyzer")
    st.multiselect("Select Assets:", options=sorted(df_raw["CMP ID"].unique()))
    # Logic for Active Count >= 2 and clustered bar chart rendering

# TAB 2: COMPARE TWO YEARS
with tabs[2]:
    st.subheader("Compare Two Years")
    c1, c2 = st.columns(2)
    yr1 = c1.selectbox("Baseline Year", list(fy_map.keys()))
    yr2 = c2.selectbox("Target Year", list(fy_map.keys()))
    if yr1 == yr2: st.warning("Please select different years.")
    # Logic for grouped bar charts

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
