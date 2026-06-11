import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
    "FY 23-24": "#2CA02C",  # Green
    "FY 24-25": "#FFD700",  # Yellow
    "FY 25-26": "#D62728"   # Magenta
}

# --------------------------------------------------------------------
# 1. DATA INGESTION & CLEANING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    try:
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # --- Clean RAW Data Sheet (Vertical Database Format) ---
        df_raw = df_raw_dirty.copy()
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Type" in df_raw.columns:
            df_raw["Type"] = df_raw["Type"].astype(str).str.strip()
        if "Fiscal Year" in df_raw.columns:
            df_raw["Fiscal Year"] = df_raw["Fiscal Year"].astype(str).str.strip()
        if "Value" in df_raw.columns:
            df_raw["Value"] = pd.to_numeric(df_raw["Value"], errors='coerce').fillna(0.0)
            
        # Reshape the vertical format into a flat, horizontal analytical dataframe
        df_portfolio = pd.pivot_table(
            df_raw, 
            values="Value", 
            index=["CMP ID", "Cluster", "Fiscal Year"], 
            columns="Type", 
            aggfunc="sum"
        ).reset_index()
        
        # Ensure standard metric columns exist to prevent missing-key errors
        for metric in ["Rev", "Rent", "Cap"]:
            if metric not in df_portfolio.columns:
                df_portfolio[metric] = 0.0
            else:
                df_portfolio[metric] = df_portfolio[metric].fillna(0.0)
                
        # Extract available unique fiscal years directly from the column entries
        target_fys = sorted(df_portfolio["Fiscal Year"].unique().tolist())
        if not target_fys:
            target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
            
        # --- Clean Rent Data Sheet Columns and Text Metrics ---
        df_rent = df_rent_dirty.copy()
        df_rent.columns = [str(col).strip() for col in df_rent.columns]
        
        wh_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["CODE", "CMP", "WAREHOUSE", "WH", "ID"])]
        wh_code_col = wh_matches[0] if wh_matches else df_rent.columns[0]
        
        rev_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["REV", "INCOME", "BILL", "EARN", "TURN"])]
        rev_col = rev_matches[0] if rev_matches else (df_rent.columns[1] if len(df_rent.columns) > 1 else df_rent.columns[0])
        
        rent_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["RENT", "OUTFLOW", "EXPENSE", "COST", "FIXED"])]
        rent_col = rent_matches[0] if rent_matches else (df_rent.columns[2] if len(df_rent.columns) > 2 else df_rent.columns[0])
        
        df_rent["Warehouse Code Normalized"] = df_rent[wh_code_col].astype(str).str.strip().str.upper()
        df_rent["Monthly Revenue"] = pd.to_numeric(df_rent[rev_col], errors='coerce').fillna(0.0)
        df_rent["Monthly Rent"] = pd.to_numeric(df_rent[rent_col], errors='coerce').fillna(0.0)
        
        return df_portfolio, df_rent, target_fys

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse Excel sheets. Details: {str(e)}")
        st.stop()

# Repository source layout checkpoint
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_portfolio, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (POST-PIVOT PROCESSING)
# --------------------------------------------------------------------
def build_runtime_fy_dataset(fy_target):
    # Isolate data rows for the targeted year
    df_step = df_portfolio[df_portfolio["Fiscal Year"] == fy_target].copy()
    
    if df_step.empty:
        # Fallback empty dataframe matching structure to prevent interface crashes
        return pd.DataFrame(columns=["CMP ID", "Cluster", "Rev", "Rent", "Cap", "Area_SqFt", "Net_Surplus", "Rev_PSF", "Rent_PSF"])
        
    df_step["Area_SqFt"] = df_step["Cap"] * MT_TO_SQFT_CONVERSION
    df_step["Net_Surplus"] = df_step["Rev"] - df_step["Rent"]
    
    # Defensive handling for full dehires (Capacity = 0) to avoid DivisionByZero crashes
    df_step["Rev_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rev"] / df_step["Area_SqFt"], 0.0)
    df_step["Rent_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rent"] / df_step["Area_SqFt"], 0.0)
    return df_step

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.sidebar.selectbox(
    "Target Fiscal Year Focus",
    options=available_fys,
    index=available_fys.index("FY 24-25") if "FY 24-25" in available_fys else 0
)

# Extract capacity profiles matching the current chosen timeline footprint bounds
current_caps = df_portfolio[df_portfolio["Fiscal Year"] == selected_fy]["Cap"]
min_cap_val = int(current_caps.min()) if not current_caps.empty else 0
max_cap_val = int(current_caps.max()) if not current_caps.empty else 100000

capacity_range = st.sidebar.slider(
    f"Active Capacity Boundary ({selected_fy})",
    min_value=min_cap_val,
    max_value=max_cap_val,
    value=(min_cap_val, max_cap_val),
    help="CRITICAL FILTER RULE: Slider values only limit Tab 1 views. Rest of history tools remain unfiltered to preserve lifecycle context."
)

# --------------------------------------------------------------------
# 4. STRUCTURAL ARCHITECTURE (4 HIGH-PERFORMANCE TABS)
# --------------------------------------------------------------------
tabs = st.tabs([
    "📈 Portfolio Performance Summary",
    "🔄 YoY Sq. Ft. Rent Analyzer",
    "📊 Compare Two Years",
    "🔍 Individual Warehouse Drilldown"
])

# ====================================================================
# TAB 1: PORTFOLIO PERFORMANCE SUMMARY
# ====================================================================
with tabs[0]:
    st.subheader(f"Portfolio Financial & Footprint Summary Matrix — {selected_fy}")
    
    # Extract data matching the selected year layout parameters
    active_fy_df = build_runtime_fy_dataset(selected_
