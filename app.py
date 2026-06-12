import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(layout="wide")

# 2. File Uploader (Use the sidebar to swap files easily)
uploaded_file = st.sidebar.file_uploader("Upload your data", type=["xlsx", "csv"])

if uploaded_file:
    # 3. Data Loading
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
    
    df = load_data(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]

    # 4. Tabs
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # 5. Drilldown Tab with "Safety Gate"
    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        options = sorted(df["CMP ID"].dropna().unique().tolist())
        target = st.selectbox("Select Warehouse:", options=options)
        
        wh_slice = df[df["CMP ID"] == target]
        
        # GATEKEEPER: Only proceed if data exists
        if not wh_slice.empty:
            # Filter for columns that are years (2023, 2024, etc.)
            date_cols = [c for c in wh_slice.columns if any(x in str(c) for x in ["2023", "2024", "2025", "2026"])]
            
            if date_cols:
                # Use a simple line chart which is much more stable than manual figure construction
                fig = px.line(wh_slice[date_cols].T, title=f"Trend for {target}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No date-based columns found.")
        else:
            st.warning("No data found for this selection.")

else:
    st.info("Please upload your data file in the sidebar to get started.")
