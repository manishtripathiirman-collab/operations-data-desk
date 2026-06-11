import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

st.set_page_config(page_title="Warehouse Performance Analyzer", layout="wide")

# ---------------------------------------------------------
# 1. DATA INGESTION & PROCESSING
# ---------------------------------------------------------
@st.cache_resource
def load_and_process():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    
    # Identify monthly date columns
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, date_cols

df_raw, chronological_months = load_and_process()

# ---------------------------------------------------------
# 2. TABS & UI
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Financial Overview")
    st.info("Aggregating horizontal matrix data...")
    # Add your Tab 0 charts/metrics here using filtered df_raw

# TAB 1: YoY RENT ANALYZER
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Analyzer")
    st.info("Visualizing PSF trends for seasoned assets.")

# TAB 2: COMPARE TWO YEARS
with tabs[2]:
    st.subheader("Compare Two Years")
    st.info("Select two years from the sidebar to cross-examine.")

# TAB 3: WAREHOUSE DRILLDOWN
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target_wh = st.selectbox("Select Facility:", options=sorted(df_raw["CMP ID"].unique()))
    
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    rev_row = wh_slice[wh_slice["Type_Clean"].str.contains("rev", na=False)]
    rent_row = wh_slice[wh_raw_slice["Type_Clean"].str.contains("rent", na=False)]
    
    if not rev_row.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chronological_months, y=rev_row[chronological_months].values.flatten(), name="Revenue"))
        fig.add_trace(go.Scatter(x=chronological_months, y=rent_row[chronological_months].values.flatten(), name="Rent"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for this facility.")
