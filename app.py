import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Upload your Excel file to begin.")
    st.stop()

@st.cache_data
def load_and_transform(file):
    df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Standardize first column
    df = df.rename(columns={df.columns[0]: 'Warehouse'})
    
    # MELT: Turn month-columns into a 'Date' and 'Metric' structure
    df_long = df.melt(id_vars=['Warehouse'], var_name='Metric_Date', value_name='Amount')
    
    # SPLIT: Separate '2023-04-01 00:00:00' and 'Rent'
    # This regex looks for date patterns
    df_long['Date'] = pd.to_datetime(df_long['Metric_Date'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0])
    df_long['Metric'] = df_long['Metric_Date'].str.replace(r'\d{4}-\d{2}-\d{2}', '', regex=True).str.strip()
    
    return df_long

df_long = load_and_transform(uploaded_file)
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY (The Math)
with tabs[0]:
    st.subheader("Portfolio Performance")
    # Pivot so we have columns for Rent, Rev, Capacity
    pivot = df_long.pivot_table(index='Warehouse', columns='Metric', values='Amount', aggfunc='sum')
    
    # Apply PSF Logic (MT * 6)
    total_cap = pivot.filter(like='Capacity').sum().sum()
    total_sqft = total_cap * 6
    st.metric("Total Sq. Ft. (Capacity * 6)", f"{total_sqft:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Warehouse Drilldown")
    target = st.selectbox("Select Warehouse", sorted(df_long['Warehouse'].unique()))
    slice_data = df_long[df_long['Warehouse'] == target]
    st.line_chart(slice_data, x='Date', y='Amount', color='Metric')
