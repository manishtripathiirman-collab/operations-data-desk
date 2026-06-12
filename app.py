import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["xlsx", "csv"])

if uploaded_file:
    # 2. DATA ENGINE: Load and Normalize (The "Fix")
    @st.cache_data
    def process_data(file):
        raw_df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        # Use the first row as headers, then clean
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        
        # Identify Warehouse ID (First Column)
        id_col = raw_df.columns[0]
        
        # Prepare for reshaping
        df_cleaned = raw_df.iloc[1:].copy()
        df_cleaned = df_cleaned.rename(columns={id_col: 'Warehouse_ID'})
        
        # Melt/Normalize the data into a Long Format
        # This creates columns: 'Warehouse_ID', 'Metric', 'Value'
        df_long = pd.melt(df_cleaned, id_vars=['Warehouse_ID'], var_name='Month_Metric', value_name='Value')
        
        # Split Month_Metric into 'Month' and 'Metric'
        df_long[['Month', 'Metric']] = df_long['Month_Metric'].str.extract(r'(.*)\s+(.*)')
        
        return df_long

    df_long = process_data(uploaded_file)
    
    # 3. TABS
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # TAB 1: PORTFOLIO SUMMARY
    with tabs[0]:
        st.subheader("Portfolio Performance")
        # Pivot the long data to get clean totals
        summary = df_long.pivot_table(index='Metric', values='Value', aggfunc='sum')
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"₹{summary.loc['Rev', 'Value']:,.0f}")
        c2.metric("Total Rent", f"₹{summary.loc['Rent', 'Value']:,.0f}")
        # Spatial Math: Total Capacity * 6
        total_sqft = summary.loc['Capacity', 'Value'] * 6
        c3.metric("Total Area Leased", f"{total_sqft:,.0f} Sq. Ft.")

    # TAB 4: DRILLDOWN
    with tabs[3]:
        st.subheader("Warehouse Drilldown")
        target = st.selectbox("Select Warehouse:", options=sorted(df_long['Warehouse_ID'].unique()))
        
        wh_data = df_long[df_long['Warehouse_ID'] == target]
        
        # Simple, stable rendering
        st.line_chart(wh_data.pivot(index='Month', columns='Metric', values='Value'))

else:
    st.info("Please upload your file in the sidebar to begin.")
