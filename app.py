import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# --------------------------------------------------------------------
# 1. DATA INGESTION & PROCESSING
# --------------------------------------------------------------------
@st.cache_resource
def load_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    
    date_cols = [c for c in df.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, date_cols

df_raw, chronological_months = load_data()

# --------------------------------------------------------------------
# 2. TABS & LOGIC
# --------------------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Financial Overview")
    st.write("Summary data based on RAW Data columns.")
    st.dataframe(df_raw.head())

# TAB 1: YoY RENT ANALYZER
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Analyzer")
    st.write("Rent trends across fiscal years will populate here.")

# TAB 2: COMPARE YEARS
with tabs[2]:
    st.subheader("Compare Two Years")
    c1, c2 = st.columns(2)
    yr1 = c1.selectbox("Baseline Year", ["FY 23-24", "FY 24-25", "FY 25-26"])
    yr2 = c2.selectbox("Target Year", ["FY 23-24", "FY 24-25", "FY 25-26"])
    st.write("Comparative analysis metrics will populate here.")

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
        st.warning("No data for this facility.")
