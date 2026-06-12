import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Config
st.set_page_config(layout="wide")

# 2. File Uploader (Sidebar)
uploaded_file = st.sidebar.file_uploader("Upload Data File", type=["xlsx", "csv"])

if uploaded_file:
    # 3. Load Data
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    df = load_data(uploaded_file)
    
    # 4. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # --- DRILLDOWN TAB (The one causing errors) ---
    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        options = sorted(df["CMP ID"].dropna().unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        wh_slice = df[df["CMP ID"] == target]
        
        # GATEKEEPER: Only proceed if data is not empty
        if not wh_slice.empty:
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                # Use simple chart to prevent Layout errors
                fig = px.line(wh_slice[date_cols].T, title=f"Trends for {target}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No date-based columns found.")
        else:
            st.warning("Data slice is empty.")

    # --- OTHER TABS (Safe Placeholders) ---
    with tabs[0]: st.write("Portfolio Summary: Awaiting Logic...")
    with tabs[1]: st.write("YoY Analysis: Awaiting Logic...")
    with tabs[2]: st.write("Compare Years: Awaiting Logic...")

else:
    st.info("Please upload your Excel/CSV file in the sidebar to start.")
