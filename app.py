import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.info("Upload your CSV file.")
    st.stop()

@st.cache_data
def load_data(file):
    # Read raw headers to create unique triplet names
    raw_header = pd.read_csv(file, nrows=0)
    new_cols = [raw_header.columns[0]]
    
    # Create unique names: Date_Cap, Date_Rent, Date_Rev
    for i in range((len(raw_header.columns) - 1) // 3):
        date = raw_header.columns[1 + (i*3)]
        new_cols.extend([f"{date}_Cap", f"{date}_Rent", f"{date}_Rev"])
    
    df = pd.read_csv(file, names=new_cols, header=1)
    return df

df = load_data(uploaded_file)
wh_col = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Capacity * 6 = Sq Ft
    total_mt = df.filter(like="_Cap").sum().sum()
    total_rev = df.filter(like="_Rev").sum().sum()
    total_rent = df.filter(like="_Rent").sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area", f"{total_mt * 6:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[wh_col].unique())
    slice_df = df[df[wh_col] == target]
    
    if not slice_df.empty:
        # Show trends
        st.line_chart(slice_df.filter(like="_Rev").T, width=0, height=300)
        st.line_chart(slice_df.filter(like="_Rent").T, width=0, height=300)
