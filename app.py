import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. File Uploader
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["csv", "xlsx"])

if uploaded_file:
    # 2. Load & Process Data
    @st.cache_data
    def load_and_prep(file):
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    df = load_and_prep(uploaded_file)
    
    # 3. Setup Tabs
    tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent", "📊 Compare Years", "🔍 Warehouse Drilldown"])

    # TAB 1: PORTFOLIO PERFORMANCE
    with tabs[0]:
        st.subheader("Portfolio Performance Summary")
        # Identify Capacity, Rent, and Rev columns (using substrings)
        cap_cols = [c for c in df.columns if "Capacity" in c]
        total_mt = df[cap_cols].sum().sum()
        total_sqft = total_mt * 6
        st.metric("Total Unique Storage (Sq. Ft.)", f"{total_sqft:,.0f} Sq. Ft.")

    # TAB 2: YoY RENT ANALYZER
    with tabs[1]:
        st.subheader("YoY Sq. Ft. Rent Analyzer")
        st.info("Seasoned Asset Filter: Calculating rates using (Rent / (Capacity * 6))")
        # Add your multiselect here
        selected = st.multiselect("Select Assets:", df.iloc[:,0].unique())

    # TAB 3: COMPARE TWO YEARS
    with tabs[2]:
        st.subheader("Compare Two Years")
        col1, col2 = st.columns(2)
        y1 = col1.selectbox("Baseline Year", ["2023", "2024", "2025"])
        y2 = col2.selectbox("Target Year", ["2024", "2025", "2026"])
        st.write("Overlay logic active.")

    # TAB 4: DRILLDOWN
    with tabs[3]:
        st.subheader("Individual Drilldown")
        target = st.selectbox("Select Warehouse:", df.iloc[:,0].unique())
        slice_df = df[df.iloc[:,0] == target]
        
        # GATEKEEPER: Prevent crashes
        if not slice_df.empty:
            # Melt data for plotting
            st.line_chart(slice_df.iloc[:, 1:].T)
        else:
            st.warning("No data.")

else:
    st.info("Upload your Excel/CSV file to the sidebar to initialize the dashboard.")
