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
    "FY 23-24": "#2CA02C",  # Green
    "FY 24-25": "#FFD700",  # Yellow
    "FY 25-26": "#D62728"   # Magenta
}

# Helper to clean and group cluster names automatically from CMP ID strings
def clean_cluster_name(cmp_id):
    match = re.match(r'^([a-zA-Z\s\-\(\)]+)', str(cmp_id))
    if match:
        return match.group(1).strip().upper()
    return "STANDARD-GROUP"

# --------------------------------------------------------------------
# 1. HORIZONTAL MATRIX DATA INGESTION & PROCESSING LAYER
# --------------------------------------------------------------------
@st.cache_resource
def load_and_clean_warehouse_data(file_path):
    try:
        # Load rows directly from worksheet matrix
        df_raw = pd.read_excel(file_path, sheet_name="RAW Data")
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        df_raw["Cluster"] = df_raw["CMP ID"].apply(clean_cluster_name)
        df_raw["Type_Clean"] = df_raw["Details"].astype(str).str.strip().str.lower()
        
        # Isolate chronological monthly tracking columns from metadata headers
        date_cols = []
        for col in df_raw.columns:
            if col.startswith("2023") or col.startswith("2024") or col.startswith("2025") or col.startswith("2026"):
                date_cols.append(col)
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
                
        # Group single month columns into true Indian Fiscal Years (April to March)
        fy_groups = {
            "FY 23-24": [c for c in date_cols if (c >= "2023-04-01" and c <= "2024-03-01")],
            "FY 24-25": [c for c in date_cols if (c >= "2024-04-01" and c <= "2025-03-01")],
            "FY 25-26": [c for c in date_cols if (c >= "2025-04-01" and c <= "2026-03-01")]
        }
        
        unique_warehouses = df_raw["CMP ID"].unique()
        portfolio_records = []
        
        for cid in unique_warehouses:
            wh_rows = df_raw[df_raw["CMP ID"] == cid]
            cluster_val = wh_rows["Cluster"].iloc[0]
            
            # Map clean rows based on exact tokens present in details index
            rev_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rev|revenue|income", na=False)]
            rent_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rent|fixed", na=False)]
            cap_rows = wh_rows[wh_rows["Type_Clean"].str.contains("cap|capacity|space", na=False)]
            
            for fy_name, columns_in_fy in fy_groups.items():
                if not columns_in_fy:
                    continue
                    
                # Financial parameters are aggregated horizontally via sum total
                rev_val = float(rev_rows[columns_in_fy].sum().sum()) if not rev_rows.empty else 0.0
                rent_val = float(rent_rows[columns_in_fy].sum().sum()) if not rent_rows.empty else 0.0
                
                # Capacity parameter maps average across active months to capture dehire timeline steps precisely
                cap_val = float(cap_rows[columns_in_fy].mean().mean()) if not cap_rows.empty else 0.0
                if np.isnan(cap_val):
                    cap_val = 0.0
                    
                portfolio_records.append({
                    "CMP ID": cid,
                    "Cluster": cluster_val,
                    "Fiscal Year": fy_name,
                    "Rev": rev_val,
                    "Rent": rent_val,
                    "Cap": cap_val
                })
                
        df_portfolio = pd.DataFrame(portfolio_records)
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        
        return df_portfolio, target_fys, df_raw, date_cols

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse raw matrix columns. Details: {str(e)}")
        st.stop()

# Repository configuration setup
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_portfolio, available_fys, df_raw_original, chronological_months = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (DEHIRE STABILIZED STRATEGY)
# --------------------------------------------------------------------
def build_runtime_fy_dataset(fy_target):
    df_step = df_portfolio[df_portfolio["Fiscal Year"] == fy_target].copy()
    
    if df_step.empty:
        return pd.DataFrame(columns=["CMP ID", "Cluster", "Rev", "Rent", "Cap", "Area_SqFt", "Net_Surplus", "Rev_PSF", "Rent_PSF"])
        
    df_step["Area_SqFt"] = df_step["Cap"] * MT_TO_SQFT_CONVERSION
    df_step["Net_Surplus"] = df_step["Rev"] - df_step["Rent"]
    
    df_step["Rev_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rev"] / df_step["Area_SqFt"], 0.0)
    df_step["Rent_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rent"] / df_step["Area_SqFt"], 0.0)
    return df_step

# Highlight styling routines to spotlight best performance margins and worst rent outflows
def spotlight_best_performers(s):
    is_max = s == s.max()
    return ['background-color: #D4EDDA; color: #155724; font-weight: bold' if v else '' for v in is_max]

def spotlight_worst_performers(s):
    is_max = s == s.max()
    return ['background-color: #F8D7DA; color: #721C24; font-weight: bold' if v else '' for v in is_max]

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

current_caps = df_portfolio[df_portfolio["Fiscal Year"] == selected_fy]["Cap"] if not df_portfolio.empty else pd.Series([0])
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
    
    active_fy_df = build_runtime_fy_dataset(selected_fy)
    
    filtered_tab1 = active_fy_df[
        (active_fy_df["Cap"] >= capacity_range[0]) & 
        (active_fy_df["Cap"] <= capacity_range[1])
    ]
    
    if filtered_tab1.empty:
        st.warning("⚠️ No warehouse allocations match the chosen Capacity range slider parameters.")
    else:
        total_rev = filtered_tab1["Rev"].sum()
        total_rent = filtered_tab1["Rent"].sum()
        net_contribution = total_rev - total_rent
        rent_efficiency = (total_rent / total_rev * 100) if total_rev > 0 else 0.0
        
        total_capacity_mt = filtered_tab1["Cap"].sum()
        total_area_sqft = total_capacity_mt * MT_TO_SQFT_CONVERSION
        
        macro_rev_psf = (total_rev / total_area_sqft) if total_area_sqft > 0 else 0.0
        macro_rent_psf = (total_rent / total_area_sqft) if total_area_sqft > 0 else 0.0
        
        # Display Row 1
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
        row1_col1.metric("Total Revenue", f"₹{total_rev:,.2f}")
        row1_col2.metric("Total Fixed Rent", f"₹{total_rent:,.2f}")
        row1_col3.metric("Net Contribution Surplus", f"₹{net_contribution:,.2f}")
        row1_col4.metric("Rent-to-Revenue Efficiency", f"{rent_efficiency:.2f}%")
        
        st.markdown("---")
        
        # Display Row 2 — Revenue integration pinned as clear context secondary marker
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row2_col1.metric("Total Area Leased", f"{total_area_sqft:,.0f} Sq. Ft.", f"₹{total
