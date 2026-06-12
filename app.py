import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. Sidebar File Uploader (Use this to swap files easily)
uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx", "csv"])

if uploaded_file:
    # 2. Data Loading
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    df = load_data(uploaded_file)
    
    # 3. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        # Identify unique IDs
        options = sorted(df["CMP ID"].dropna().unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        # FILTER: Get the specific warehouse data
        wh_slice = df[df["CMP ID"] == target]
        
        # CHECK: Is there data?
        if wh_slice.empty:
            st.warning("No data found for this selection.")
        else:
            # Only proceed if data exists
            st.write(f"Data found for {target}")
            
            # Simple line chart using Streamlit's native helper (less prone to layout crashes)
            # We filter for columns that contain 2023, 2024, 2025 or 2026
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                chart_data = wh_slice[date_cols].T
                st.line_chart(chart_data)
            else:
                st.info("No date-based columns found to plot.")

else:
    st.info("Please upload your Excel file using the sidebar.")
