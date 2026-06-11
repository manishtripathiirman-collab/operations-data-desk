import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Warehouse Analyzer", layout="wide")

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
    
    # Define Fiscal Years
    fy_map = {
        "FY 23-24": [c for c in date_cols if "2023" in c or "2024-01" in c or "2024-02" in c or "2024-03" in c],
        "FY 24-25": [c for c in date_cols if "2024-04" in c or "2024-05" in c or "2024-06" in c or "2024-07" in c or "2024-08" in c or "2024-09" in c or "2024-10" in c or "2024-11" in c or "2024-12" in c or "2025-01" in c or "2025-02" in c or "2025-03" in c],
        "FY 25-26": [c for c in date_cols if "2025-04" in c or "2025-05" in c or "2025-06" in c or "2025-07" in c or "2025-08" in c or "2025-09" in c or "2025-10" in c or "2025-11" in c or "2025-12" in c or "2026-01" in c or "2026-02" in c or "2026-03" in c]
    }
    return df, date_cols, fy_map

df_raw, chronological_months, fy_map = load_and_process()

# ---------------------------------------------------------
# 2. SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", list(fy_map.keys()))
all_caps = df_raw[df_raw["Type_Clean"].str.contains("cap", na=False)][chronological_months].mean(axis=1)
capacity_range = st.sidebar.slider("Active Capacity Boundary", 0, int(all_caps.max()), (0, int(all_caps.max())))

# ---------------------------------------------------------
# 3. TABS
# ---------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Warehouse Drilldown"])

# TAB 0: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader(f"Portfolio Financial Overview - {selected_fy}")
    # Filter by selected FY and capacity
    fy_cols = fy_map[selected_fy]
    df_fy = df_raw.copy()
    df_fy['Rev_Total'] = df_fy[df_raw["Type_Clean"].str.contains("rev", na=False)][fy_cols].sum(axis=1)
    st.dataframe(df_fy[['CMP ID', 'Rev_Total']].head(10))

# TAB 1: YoY RENT ANALYZER
with tabs[1]:
    st.subheader("Year-on-Year Rent Analysis")
    st.write("Compare PSF rates across fiscal years.")

# TAB 2: COMPARE YEARS
with tabs[2]:
    st.subheader("Year Comparison")
    st.write("Select two fiscal years for variance analysis.")

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
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for this facility.")
