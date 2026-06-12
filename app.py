import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Warehouse Portfolio Dashboard")

# 1. DATA LOADER: Handles the repeating headers in your CSV
@st.cache_data
def load_data(file):
    # Load raw data
    raw = pd.read_csv(file)
    # Reconstruct headers: [Warehouse, Date1_Cap, Date1_Rent, Date1_Rev, ...]
    new_cols = [raw.columns[0]]
    for i in range(1, len(raw.columns), 3):
        date = raw.columns[i]
        new_cols.extend([f"{date}_Cap", f"{date}_Rent", f"{date}_Rev"])
    raw.columns = new_cols
    return raw

# 2. UPLOAD UI
uploaded_file = st.sidebar.file_uploader("Upload Warehouse CSV", type=["csv"])
if not uploaded_file:
    st.title("Warehouse Portfolio Dashboard")
    st.info("Please upload your CSV file to get started.")
    st.stop()

df = load_data(uploaded_file)
wh_col = df.columns[0]

# 3. TABS
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Comparison Tool", "🔍 Warehouse Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Math: MT * 6 = Sq Ft
    total_sqft = df.filter(like="_Cap").sum().sum() * 6
    total_rev = df.filter(like="_Rev").sum().sum()
    total_rent = df.filter(like="_Rent").sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Contribution", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area", f"{total_sqft:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Warehouse History")
    target = st.selectbox("Select Warehouse:", df[wh_col].unique())
    slice_df = df[df[wh_col] == target]
    
    # Revenue & Rent Trends
    st.line_chart(slice_df.filter(like="_Rev").T, title="Revenue History")
    st.line_chart(slice_df.filter(like="_Rent").T, title="Rent History")
