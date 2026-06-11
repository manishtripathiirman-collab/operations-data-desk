import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PAGE LAYOUT CONFIGURATION
st.set_page_config(layout="wide", page_title="Operations Data Desk")

st.title("📊 Operations Data Desk")
st.markdown("### Warehouse Rent & Performance Dashboard")
st.markdown("---")

# 2. LOAD DATA DIRECTLY FROM YOUR EXCEL WORKBOOK (.XLSX)
@st.cache_data
def load_excel_data():
    # Explicitly uses openpyxl to process your Excel sheets cleanly
    raw_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data", engine="openpyxl")
    rent_details_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="Rent Data", engine="openpyxl")
    return raw_df, rent_details_df

try:
    df_raw, df_rent_details = load_excel_data()
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
    st.info("Please ensure 'Rent Analysis Data.xlsx' is in your root folder and contains 'RAW Data' and 'Rent Data' sheets.")
    st.stop()

# 3. SIDEBAR FILTER OPTIONS
st.sidebar.header("Filter Options")
selected_fy = st.sidebar.selectbox("Select Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)

# 4. PRIMARY KPI METRIC CARDS
total_rent = df_raw[df_raw["Details"] == "Rent"][selected_fy].sum()
total_rev = df_raw[df_raw["Details"] == "Rev"][selected_fy].sum()
net_surplus = total_rev - total_rent

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Revenue", f"₹{total_rev:,.0f}")
kpi2.metric("Total Rent Cost", f"₹{total_rent:,.0f}")
kpi3.metric("Net Surplus", f"₹{net_surplus:,.0f}")

st.markdown("---")

# 5. CORE ANALYTICAL VISUALIZATIONS
col1, col2 = st.columns(2)
with col1:
    st.subheader("Warehouse Capacity Distribution")
    fig_cap = px.bar(df_raw.drop_duplicates(subset=["CMP ID"]), x="CMP ID", y="Capacity", title="Capacity by Warehouse ID")
    st.plotly_chart(fig_cap, use_container_width=True)

with col2:
    st.subheader("Revenue vs Rent Trends")
    pivoted = df_raw.pivot_table(index=["CMP ID"], columns="Details", values=selected_fy).reset_index()
    if "Rent" in pivoted.columns and "Rev" in pivoted.columns:
        fig_trend = px.scatter(pivoted, x="Rent", y="Rev", hover_name="CMP ID", trendline="ols", title="Rent to Revenue Mapping")
        st.plotly_chart(fig_trend, use_container_width=True)

# 6. GRANULAR DATA PREVIEW
st.markdown("---")
st.subheader("📋 Complete Data View")
st.dataframe(df_raw)
