import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data", type=["csv", "xlsx"])
if not uploaded_file:
    st.info("Upload your CSV or Excel file.")
    st.stop()

@st.cache_data
def load_and_transform(file):
    # Read raw data
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    # 2. FLATTEN THE "WIDE" DATA
    # We rename columns to be unique triplets: Date_Cap, Date_Rent, Date_Rev
    new_cols = [df.columns[0]] # Keep the Warehouse ID
    # Assume every 3 columns after the ID are Capacity, Rent, Rev
    for i in range(1, len(df.columns), 3):
        date = df.columns[i]
        new_cols.extend([f"{date}_Cap", f"{date}_Rent", f"{date}_Rev"])
    
    df.columns = new_cols
    return df

df = load_and_transform(uploaded_file)
wh_id = df.columns[0]

# 3. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY (Safe Math)
with tabs[0]:
    st.subheader("Portfolio Performance")
    # Summing triplets across all dates
    total_sqft = df.filter(like="_Cap").sum().sum() * 6
    total_rev = df.filter(like="_Rev").sum().sum()
    total_rent = df.filter(like="_Rent").sum().sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Total Area", f"{total_sqft:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    target = st.selectbox("Select Warehouse:", options=df[wh_id].unique())
    slice_df = df[df[wh_id] == target]
    
    # Plot Revenue (Rev) and Rent
    st.subheader("Revenue vs Rent History")
    st.line_chart(slice_df.filter(like="_Rev").T)
    st.line_chart(slice_df.filter(like="_Rent").T)
