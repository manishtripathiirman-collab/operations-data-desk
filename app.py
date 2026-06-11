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
        
        # Clean RAW Data sheet columns and structural spacing anomalies
        df_raw = df_raw_dirty.copy()
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Type" in df_raw.columns:
            df_raw["Type"] = df_raw["Type"].astype(str).str.strip()
            
        # Standard target fiscal tracking horizons
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        for fy in target_fys:
            if fy in df_raw.columns:
                df_raw[fy] = pd.to_numeric(df_raw[fy], errors='coerce').fillna(0.0)
            else:
                df_raw[fy] = 0.0
                
        # Clean Rent Data sheet columns and text metrics
        df_rent = df_rent_dirty.copy()
        df_rent.columns = [str(col).strip() for col in df_rent.columns]
        
        wh_code_col = [c for c in df_rent.columns if "CODE" in c.upper() or "CMP" in c.upper() or "WAREHOUSE" in c.upper()][0]
        rev_col = [c for c in df_rent.columns if "REV" in c.upper()][0]
        rent_col = [c for c in df_rent.columns if "RENT" in c.upper()][0]
        
        df_rent["Warehouse Code Normalized"] = df_rent[wh_code_col].astype(str).str.strip().str.upper()
        df_rent["Monthly Revenue"] = pd.to_numeric(df_rent[rev_col], errors='coerce').fillna(0.0)
        df_rent["Monthly Rent"] = pd.to_numeric(df_rent[rent_col], errors='coerce').fillna(0.0)
        
        return df_raw, df_rent, target_fys

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse Excel sheets. Details: {str(e)}")
        st.stop()

# Repository source layout checkpoint
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_raw, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (BULLETPROOF MASKING STRATEGY)
# --------------------------------------------------------------------
def build_runtime_fy_dataset(fy_target):
    # Dynamically extract tracking variables mapped exactly to horizontal rows
    rev_df = df_raw[df_raw["Type"] == "Rev"]
    rent_df = df_raw[df_raw["Type"] == "Rent"]
    cap_df = df_raw[df_raw["Type"] == "Cap"]
    
    # Extract unique facilities to map coordinates safely
    unique_facilities = df_raw.drop_duplicates(subset=["CMP ID"]).copy()
    
    records = []
    for _, f in unique_facilities.iterrows():
        cid = f["CMP ID"]
        cluster = f["Cluster"]
        
        # Filter down to the specific warehouse code to prevent lookup duplication crashes
        rev_match = rev_df[rev_df["CMP ID"] == cid][fy_target]
        rent_match = rent_df[rent_df["CMP ID"] == cid][fy_target]
        cap_match = cap_df[cap_df["CMP ID"] == cid][fy_target]
        
        # Sum up values if duplicates exist, otherwise get the safe baseline float value
        rev_val = float(rev_match.sum()) if not rev_match.empty else 0.0
        rent_val = float(rent_match.sum()) if not rent_match.empty else 0.0
        cap_val = float(cap_match.sum()) if not cap_match.empty else 0.0
        
        area_val = cap_val * MT_TO_SQFT_CONVERSION
        net_surplus = rev_val - rent_val
        
        # Protective division boundaries for full dehires (Capacity = 0)
        rev_psf = (rev_val / area_val) if area_val > 0 else 0.0
        rent_psf = (rent_val / area_val) if area_val > 0 else 0.0
        
        records.append({
            "CMP ID": cid,
            "Cluster": cluster,
            "Rev": rev_val,
            "Rent": rent_val,
            "Cap": cap_val,
            "Area_SqFt": area_val,
            "Net_Surplus": net_surplus,
            "Rev_PSF": rev_psf,
            "Rent_PSF": rent_psf
        })
        
    return pd.DataFrame(records)

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.sidebar.selectbox(
    "Target Fiscal Year Focus",
    options=available_fys,
    index=min(1, len(available_fys)-1) if available_fys else 0
)

# Extract changing capacity profiles matching current chosen timeline footprint bounds
current_caps = df_raw[df_raw["Type"] == "Cap"][selected_fy]
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
    
    # Extract dynamic runtime dataset matching your raw design metrics
    active_fy_df = build_runtime_fy_dataset(selected_fy)
    
    # Apply filter rule strictly to Tab 1 assets
    filtered_tab1 = active_fy_df[
        (active_fy_df["Cap"] >= capacity_range[0]) & 
        (active_fy_df["Cap"] <= capacity_range[1])
    ]
    
    if filtered_tab1.empty:
        st.warning("⚠️ No warehouse allocations match the chosen Capacity range slider parameters.")
    else:
        # High-Impact Performance Metrics Calculation
        total_rev = filtered_tab1["Rev"].sum()
        total_rent = filtered_tab1["Rent"].sum()
        total_surplus = filtered_tab1["Net_Surplus"].sum()
        rent_efficiency = (total_rent / total_rev * 100) if total_rev > 0 else 0.0
        
        total_area_
