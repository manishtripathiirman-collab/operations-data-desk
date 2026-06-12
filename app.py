import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload your Warehouse Excel", type=["xlsx", "csv"])

if uploaded_file:
    # 2. DATA TRANSFORMATION ENGINE
    @st.cache_data
    def load_and_transform(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        
        # A. Rename first column to 'Warehouse' to standardize
        df = df.rename(columns={df.columns[0]: 'Warehouse'})
        
        # B. Melt from "Wide" to "Long"
        # This converts those month-columns into a single 'Date_Metric' column
        df_long = df.melt(id_vars=['Warehouse'], var_name='Metric', value_name='Value')
        
        # C. Split Metric column: "2023-04-01 Capacity" -> Date: 2023-04-01, Type: Capacity
        df_long['Date'] = df_long['Metric'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0]
        df_long['Type'] = df_long['Metric'].str.replace(r'\d{4}-\d{2}-\d{2}', '', regex=True).str.strip()
        
        return df_long

    df_long = load_and_transform(uploaded_file)

    # 3. TABS
    tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

    # 4. DRILLDOWN (Now works because we have a standard 'Warehouse' column)
    with tabs[3]:
        st.subheader("Individual Warehouse Drilldown")
        target = st.selectbox("Select Warehouse:", options=sorted(df_long['Warehouse'].unique()))
        
        slice_data = df_long[df_long['Warehouse'] == target]
        
        # Simple Plotly Express chart
        fig = px.line(slice_data, x='Date', y='Value', color='Type', title=f"History: {target}")
        st.plotly_chart(fig, use_container_width=True)

    # 5. PORTFOLIO SUMMARY (The Math)
    with tabs[0]:
        st.subheader("Portfolio Financial Overview")
        # Pivot table to sum metrics
        summary = df_long.pivot_table(index='Type', values='Value', aggfunc='sum')
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"₹{summary.loc['Rev', 'Value']:,.0f}")
        c2.metric("Total Rent", f"₹{summary.loc['Rent', 'Value']:,.0f}")
        # Spatial Math: Total Capacity * 6
        total_mt = summary.loc['Capacity', 'Value']
        c3.metric("Total Sq. Ft.", f"{total_mt * 6:,.0f} Sq. Ft.")

else:
    st.info("Please upload your file in the sidebar.")
