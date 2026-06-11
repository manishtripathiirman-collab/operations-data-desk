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
# 1. DATA INGESTION & DATE-TO-FY MAPPING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    try:
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # --- Clean RAW Data Sheet (Monthly Column Matrix) ---
        df_raw = df_raw_dirty.copy()
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        else:
            df_raw["Cluster"] = "Standard-Group"
            
        if "Details" in df_raw.columns:
            df_raw["Details"] = df_raw["Details"].astype(str).str.strip()
        else:
            df_raw["Details"] = "Unknown"
            
        df_raw["Type_Clean"] = df_raw["Details"].astype(str).str.lower()
        
        # Identify monthly date tracking columns dynamically
        date_cols = []
        for col in df_raw.columns:
            if col.startswith("2023") or col.startswith("2024") or col.startswith("2025") or col.startswith("2026"):
                date_cols.append(col)
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
                
        # Define Fiscal Year date buckets (April to March cycles)
        fy_groups = {
            "FY 23-24": [c for c in date_cols if (c >= "2023-04-01" and c <= "2024-03-01")],
            "FY 24-25": [c for c in date_cols if (c >= "2024-04-01" and c <= "2025-03-01")],
            "FY 25-26": [c for c in date_cols if (c >= "2025-04-01" and c <= "2026-03-01")]
        }
        
        # Reshape vertical tracking types into horizontal summary arrays
        unique_warehouses = df_raw["CMP ID"].unique()
        portfolio_records = []
        
        for cid in unique_warehouses:
            wh_rows = df_raw[df_raw["CMP ID"] == cid]
            cluster_val = wh_rows["Cluster"].iloc[0] if "Cluster" in wh_rows.columns else "Standard-Group"
            
            rev_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rev|revenue|income", na=False)]
            rent_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rent|fixed", na=False)]
            cap_rows = wh_rows[wh_rows["Type_Clean"].str.contains("cap|capacity|space", na=False)]
            
            for fy_name, columns_in_fy in fy_groups.items():
                if not columns_in_fy:
                    continue
                    
                rev_val = float(rev_rows[columns_in_fy].sum().sum()) if not rev_rows.empty else 0.0
                rent_val = float(rent_rows[columns_in_fy].sum().sum()) if not rent_rows.empty else 0.0
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
        
        # --- Clean Rent Data Sheet ---
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
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to process raw matrix timeline. Details: {str(e)}")
        st.stop()

# Repository source layout checkpoint
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_portfolio, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (POST-GROUPING STRATEGY)
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

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.
