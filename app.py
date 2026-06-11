# --------------------------------------------------------------------
# 1. DATA INGESTION & ROBUST CLEANING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    # Safe multi-sheet reading from uploaded source file
    try:
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # Clean RAW Data sheet columns and spaces
        df_raw = df_raw_dirty.copy()
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Type" in df_raw.columns:
            df_raw["Type"] = df_raw["Type"].astype(str).str.strip()
            
        # Target financial and capacity columns natively
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        for fy in target_fys:
            if fy in df_raw.columns:
                df_raw[fy] = pd.to_numeric(df_raw[fy], errors='coerce').fillna(0.0)
            else:
                df_raw[fy] = 0.0
                
        # Clean Rent Data sheet columns and titles
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
