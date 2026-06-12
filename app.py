import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload your Warehouse Excel", type=["xlsx", "csv"])

if uploaded_file:
    # 2. TRANSFORMER (Fixes the Wide format automatically)
    @st.cache_data
    def load_and_transform(file):
        df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
        
        # Melt the data: Convert month columns into Date/Metric/Value rows
        # This makes it "Long" format, which prevents all those ValueErrors
        df_long = df.melt(id_vars=[df.columns[0]], var_name='Metric_Date', value_name='Amount')
        
        # Split '2023-04-01 Capacity' into 'Date' and 'Metric'
        df_long['Date'] = pd.to_datetime(df_long['Metric_Date'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0])
        df_long['Metric'] = df_long['Metric_Date'].str.replace(r'\d{4}-\d{2}-\d{2}', '', regex=True).str.strip()
        df_long = df_long.rename(columns={df.columns[0]: 'Warehouse'})
        return df_long

    df = load_and_transform(uploaded_file)
    
    # 3. TABS
    tabs = st.tabs(["📈 Portfolio", "🔍 Drilldown"])

    # PORTFOLIO SUMMARY
    with tabs[0]:
        st.subheader("Portfolio Financial Performance")
        summary = df.pivot_table(index='Metric', values='Amount', aggfunc='sum')
        
        # Math for Metric Tiles
        rev = summary.loc['Rev', 'Amount'] if 'Rev' in summary.index else 0
        rent = summary.loc['Rent', 'Amount'] if 'Rent' in summary.index else 0
        cap = summary.loc['Capacity', 'Amount'] if 'Capacity' in summary.index else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"₹{rev:,.0f}")
        col2.metric("Total Rent", f"₹{rent:,.0f}")
        col3.metric("Total Capacity (Sq. Ft.)", f"{cap*6:,.0f} Sq. Ft.")

    # DRILLDOWN
    with tabs[1]:
        st.subheader("Warehouse Drilldown")
        target = st.selectbox("Select Warehouse:", df['Warehouse'].unique())
        slice_data = df[df['Warehouse'] == target]
        fig = px.line(slice_data, x='Date', y='Amount', color='Metric', title=f"Performance: {target}")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload your Excel file in the sidebar to begin.")
