import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# --------------------------------------------------------------------
# 0. APP CONFIGURATION & CONSTANTS
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Warehouse Performance & Dehire Analyzer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

MT_TO_SQFT_CONVERSION = 6.0
FY_COLORS = {
    "FY 23-24": "#2CA02C", 
    "FY 24-25": "#FFD700", 
    "FY 25-26": "#D62728"
}

def clean_cluster_name(cmp_id):
    match = re.match(r'^([a-zA-Z\s\-\(\)]+)', str(cmp_id))
    return match.group(1).strip().upper() if match else "STANDARD-GROUP"

# --------------------------------------------------------------------
# 1. DATA INGESTION
# --------------------------------------------------------------------
@st.cache_resource
def load_and_clean_warehouse_data(file_path):
    df_raw = pd.read_excel(file_path, sheet_name="RAW Data")
    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
    df_raw["Cluster"] = df_raw["CMP ID"].apply(clean_cluster_name)
    df_raw["Type_Clean"] = df_raw["Details"].astype(str).str.strip().str.lower()
    
    date_cols = [c for c in df_raw.columns if str(c).startswith(("2023", "2024", "2025", "2026"))]
    for col in date_cols:
        df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
        
    return df_raw, date_cols

df_raw_original, chronological_months = load_and_clean_warehouse_data("Rent Analysis Data.xlsx")

# --------------------------------------------------------------------
# 2. TABS & LOGIC
# --------------------------------------------------------------------
tabs = st.tabs(["📈 Portfolio Performance Summary", "🔄 YoY Sq. Ft. Rent Analyzer", "📊 Compare Two Years", "🔍 Individual Warehouse Drilldown"])

# ... [Tabs 0, 1, and 2 go here] ...

with tabs[3]:
    st.subheader("Granular Individual Property Footprint Lifecycle Review")
    alphabetical_codes = sorted(df_raw_original["CMP ID"].unique().tolist())
    target_wh = st.selectbox("Select Facility:", options=alphabetical_codes)
    
    wh_raw_slice = df_raw_original[df_raw_original["CMP ID"] == target_wh]
    
    if wh_raw_slice.empty:
        st.info("No data found for this asset.")
    else:
        rev_row = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("rev|revenue|income", na=False)]
        rent_row = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("rent|fixed", na=False)]
        cap_row = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("cap|capacity|space", na=False)]
        
        rev_vals = [float(rev_row[m].iloc[0]) if not rev_row.empty else 0.0 for m in chronological_months]
        rent_vals = [float(rent_row[m].iloc[0]) if not rent_row.empty else 0.0 for m in chronological_months]
        cap_vals = [float(cap_row[m].iloc[0]) if not cap_row.empty else 0.0 for m in chronological_months]
        
        # DEFENSIVE CHECK: Only render if we have data to plot
        if sum(rev_vals) == 0 and sum(rent_vals) == 0 and sum(cap_vals) == 0:
            st.info("No active records found for this facility.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chronological_months, y=rev_vals, name='Revenue (₹)'))
            fig.add_trace(go.Scatter(x=chronological_months, y=rent_vals, name='Rent (₹)'))
            fig.add_trace(go.Scatter(x=chronological_months, y=cap_vals, name='Capacity (MT)', yaxis='y2'))
            
            # SAFE LAYOUT UPDATE
            fig.update_layout(
                template="plotly_white",
                yaxis=dict(title="Financials (₹)"),
                yaxis2=dict(title="Capacity (MT)", overlaying='y', side='right'),
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
