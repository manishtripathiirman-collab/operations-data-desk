import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ---------------------------------------------------------
# 0. CONFIG & SIDEBAR
# ---------------------------------------------------------
st.set_page_config(page_title="Warehouse Analyzer", layout="wide")

st.sidebar.title("⚙️ Global Audit Controls")
# Sidebar controls restored
selected_fy = st.sidebar.selectbox("Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"])

# ---------------------------------------------------------
# 1. DATA INGESTION
# ---------------------------------------------------------
@st.cache_resource
def load_and_process():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, date_cols

df_raw, chronological_months = load_and_process()

# Capacity slider restored
all_caps = df_raw[df_raw["Type_Clean"].str.contains("cap", na=False)][chronological_months].mean(axis=1)
capacity_range = st.sidebar.slider("Active Capacity Boundary", 0, int(all_caps.max()), (0, int(all_caps.max())))

# ---------------------------------------------------------
# 2. TABS & LOGIC
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

with tabs[0]:
    st.subheader("Portfolio Financial Overview")
    st.write("Dashboard active.")

with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Analyzer")

with tabs[2]:
    st.subheader("Compare Two Years")

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
        st.warning("No data for this facility.")
