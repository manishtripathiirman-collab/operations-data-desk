import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. UPLOAD & PREP
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Upload your Excel file to begin.")
    st.stop()

@st.cache_data
def load_and_transform(file):
    df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
    df.columns = [str(c).strip() for c in df.columns]
    # Transform from wide to long: Creates 'Warehouse', 'Date', 'Type', 'Value'
    # This is the secret to making the YoY and PSF math work
    df = df.melt(id_vars=[df.columns[0]], var_name='Metric', value_name='Amount')
    df['Date'] = pd.to_datetime(df['Metric'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0], errors='coerce')
    df['Type'] = df['Metric'].str.replace(r'\d{4}-\d{2}-\d{2}', '', regex=True).str.strip()
    return df

df_long = load_and_transform(uploaded_file)
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Math: Pivot the long data back to wide for summary
    summary = df_long.pivot_table(index='Type', values='Amount', aggfunc='sum')
    rev = summary.loc['Rev', 'Amount'] if 'Rev' in summary.index else 0
    rent = summary.loc['Rent', 'Amount'] if 'Rent' in summary.index else 0
    cap = summary.loc['Capacity', 'Amount'] if 'Capacity' in summary.index else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{rev:,.0f}")
    c2.metric("Total Rent", f"₹{rent:,.0f}")
    c3.metric("Net Surplus", f"₹{rev-rent:,.0f}")
    c4.metric("Efficiency", f"{(rent/rev)*100:.1f}%")

# TAB 4: INDIVIDUAL DRILLDOWN
with tabs[3]:
    st.subheader("Warehouse Drilldown")
    wh_col = df_long.columns[0]
    target = st.selectbox("Select Warehouse", df_long[wh_col].unique())
    slice_data = df_long[df_long[wh_col] == target]
    st.line_chart(slice_data, x='Date', y='Amount', color='Type')

# Placeholder for Tabs 2 & 3
with tabs[1]: st.write("YoY Analyzer: Use the `df_long` variable to filter by Year and calculate (Rent / (Capacity * 6))")
with tabs[2]: st.write("Comparison Tool: Use `df_long` to compare two specific date ranges.")
