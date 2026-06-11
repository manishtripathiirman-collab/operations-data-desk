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
# 1. DATA INGESTION & ROBUST CLEANING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    """
    Ingests 'RAW Data' and 'Rent Data' sheets dynamically.
    Enforces strict type coercion, handles variable capacities (dehires),
    and structures datasets for timeline-aware metric parsing.
    """
    try:
        # Load both sheets
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # --- Clean 'RAW Data' Sheet ---
        df_raw = df_raw_dirty.copy()
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Details" in df_raw.columns:
            df_raw["Details"] = df_raw["Details"].astype(str).str.strip()
            
        # Clean multi-year financial & capacity columns seamlessly
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        for fy in target_fys:
            if fy in df_raw.columns:
                df_raw[fy] = pd.to_numeric(df_raw[fy], errors='coerce').fillna(0.0)
            else:
                df_raw[fy] = 0.0
                
        # --- Clean 'Rent Data' Sheet ---
        df_rent = df_rent_dirty.copy()
        # Clean up column headers if they contain spaces
        df_rent.columns = [str(col).strip() for col in df_rent.columns]
        
        # Locate critical monthly tracking columns dynamically
        wh_code_col = [c for c in df_rent.columns if "CODE" in c.upper() or "CMP" in c.upper() or "WAREHOUSE" in c.upper()][0]
        rev_col = [c for c in df_rent.columns if "REV" in c.upper()][0]
        rent_col = [c for c in df_rent.columns if "RENT" in c.upper()][0]
        
        df_rent["Warehouse Code Normalized"] = df_rent[wh_code_col].astype(str).str.strip().str.upper()
        df_rent["Monthly Revenue"] = pd.to_numeric(df_rent[rev_col], errors='coerce').fillna(0.0)
        df_rent["Monthly Rent"] = pd.to_numeric(df_rent[rent_col], errors='coerce').fillna(0.0)
        
        return df_raw, df_rent, target_fys

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse Excel sheets. Check formatting structures. Details: {str(e)}")
        st.stop()

# Auto-loading setup from your GitHub repository folder link structure
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_raw, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. DATA PIVOTING & TRANSFORMATION ENGINE (DEHIRE PROOFED)
# --------------------------------------------------------------------
# Restructure raw rows so every warehouse has mapped rows for Rev, Rent, and Cap simultaneously
pivoted_portfolio = df_raw.pivot(index=["CMP ID", "Cluster"], columns="Type").reset_index()

def build_runtime_fy_dataset(fy_target):
    """
    Assembles a synchronized snapshot for a given fiscal year.
    Capacity is pulled as a dynamic timeline variable to
