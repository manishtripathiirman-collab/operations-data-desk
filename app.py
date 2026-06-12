import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. FILE LOADER
uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx", "csv"])

if uploaded_file:
    # 2. LOAD & CLEAN
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Identify the Warehouse column (The first column)
    wh_col = df.columns[0]
    
    # 3. TABS
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # 4. DRILLDOWN (Stable Version)
    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        target = st.selectbox("Select Warehouse:", options=sorted(df[wh_col].unique()))
        
        slice_data = df[df[wh_col] == target].iloc[0]
        
        # Only plot numeric columns
        st.line_chart(slice_data.select_dtypes(include=['number']))

    # 5. PORTFOLIO SUMMARY (The Math)
    with tabs[0]:
        st.subheader("Portfolio Performance")
        # Find all capacity columns
        cap_cols = [c for c in df.columns if "Capacity" in c]
        total_mt = df[cap_cols].sum().sum()
        total_sqft = total_mt * 6
        
        st.metric("Total Storage (Sq. Ft.)", f"{total_sqft:,.0f} Sq. Ft.")
        st.write("Math: Total MT capacity * 6")

else:
    st.info("Please upload your data file in the sidebar.")
