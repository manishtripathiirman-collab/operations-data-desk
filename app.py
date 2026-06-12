import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(layout="wide")

# 2. Sidebar File Uploader (Use this to avoid hardcoded file path issues)
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data", type=["csv", "xlsx"])

if uploaded_file:
    # 3. Load Data
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)

    df = load_data(uploaded_file)
    
    # 4. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        options = sorted(df["CMP ID"].unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        # FILTER
        wh_slice = df[df["CMP ID"] == target]
        
        # GATEKEEPER: Check if data exists BEFORE plotting
        if not wh_slice.empty:
            # Only pick columns that represent years/months
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                # Use simple Plotly Express line chart (Much more stable than go.Figure)
                fig = px.line(wh_slice[date_cols].T, title=f"Trend for {target}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No date-based columns found.")
        else:
            st.warning("No data found for this selection.")

else:
    st.info("Please upload your data file in the sidebar to get started.")
