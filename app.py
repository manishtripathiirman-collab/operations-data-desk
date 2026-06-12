import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. Setup file uploader so you never have to deal with paths again
uploaded_file = st.sidebar.file_uploader("Upload your data", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]
    
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        target = st.selectbox("Select Facility:", options=sorted(df["CMP ID"].unique()))
        wh_slice = df[df["CMP ID"] == target]
        
        # Filter for date columns (2023, 2024, 2025, 2026)
        date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
        
        # DEFENSIVE CHECK: Ensure we have data before plotting
        if not wh_slice.empty and len(date_cols) > 0:
            # Use simple native Streamlit chart (Prevents layout ValueErrors)
            st.line_chart(wh_slice[date_cols].T)
        else:
            st.warning("No data found for this facility.")
else:
    st.info("Please upload your data file in the sidebar to get started.")
