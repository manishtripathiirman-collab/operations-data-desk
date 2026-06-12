import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. Sidebar File Uploader (Always use this to swap files easily)
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data", type=["xlsx", "csv"])

if uploaded_file:
    # 2. Data Loading Engine
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        # Strip spaces from column names to prevent matching errors
        df.columns = [str(c).strip() for c in df.columns]
        return df

    df = load_data(uploaded_file)
    
    # DYNAMIC IDENTIFICATION: Pick the first column as your Warehouse/ID column
    id_col = df.columns[0]
    
    # 3. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # --- DRILLDOWN TAB ---
    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        
        # Safe options list
        options = sorted(df[id_col].dropna().unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        # FILTER
        wh_slice = df[df[id_col] == target]
        
        # GATEKEEPER: Only proceed if slice is not empty
        if not wh_slice.empty:
            # Detect date-based columns safely
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                # Transpose for plotting
                chart_data = wh_slice[date_cols].T
                chart_data.columns = [target]
                st.line_chart(chart_data)
            else:
                st.info("No date-based columns found.")
        else:
            st.warning("No data found for this selection.")

    # --- TAB 0: PORTFOLIO SUMMARY (The logic you requested) ---
    with tabs[0]:
        st.subheader("Portfolio Financial Overview")
        # Logic: Multiply Capacity by 6 to get Sq Ft
        # Note: We find columns containing 'Capacity'
        cap_cols = [c for c in df.columns if "Capacity" in c]
        total_mt = df[cap_cols].sum().sum()
        total_sqft = total_mt * 6
        
        st.metric("Total Storage Capacity (Sq. Ft.)", f"{total_sqft:,.0f} Sq. Ft.")
        st.write("Math logic applied: Total MT * 6")

else:
    st.info("Please upload your Excel/CSV file in the sidebar to begin.")
