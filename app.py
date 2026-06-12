import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. Sidebar File Uploader
uploaded_file = st.sidebar.file_uploader("Upload Data", type=["xlsx", "csv"])

if uploaded_file:
    # 2. Data Loading
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        return df

    df = load_data(uploaded_file)
    
    # Identify the warehouse column (The first column in your file)
    warehouse_col = df.columns[0]
    
    # 3. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        
        # Use the detected column name
        options = sorted(df[warehouse_col].dropna().unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        # FILTER using the detected column name
        wh_slice = df[df[warehouse_col] == target]
        
        if not wh_slice.empty:
            # Filter columns that contain date/year patterns
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                # Transpose to get Time on X-axis and Values on Y-axis
                chart_data = wh_slice[date_cols].T
                chart_data.columns = [target]
                st.line_chart(chart_data)
            else:
                st.info("No date-based columns found.")
        else:
            st.warning("No data found for this selection.")

else:
    st.info("Please upload your data file in the sidebar.")
