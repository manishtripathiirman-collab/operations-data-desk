import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. FILE LOADER
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
if not uploaded_file:
    st.info("Upload your Excel file in the sidebar to begin.")
    st.stop()

@st.cache_data
def load_and_fix(file):
    # Load headers separately to rename them
    header_df = pd.read_excel(file, nrows=0)
    
    # Generate Unique Names: Date_Cap, Date_Rent, Date_Rev
    new_cols = [header_df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    for i in range(1, len(header_df.columns), 3):
        date = str(header_df.columns[i])
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    df = pd.read_excel(file, header=1, names=new_cols)
    return df

df = load_and_fix(uploaded_file)
warehouse_id = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Spatial Metric: Sum all Capacity columns and multiply by 6
    total_mt = df.filter(like="_Cap").sum().sum()
    total_rev = df.filter(like="_Rev").sum().sum()
    total_rent = df.filter(like="_Rent").sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Sq. Ft.", f"{total_mt * 6:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[warehouse_id].unique())
    slice_df = df[df[warehouse_id] == target]
    
    if not slice_df.empty:
        # Plotting the time series for this warehouse
        rev_data = slice_df.filter(like="_Rev").T
        rent_data = slice_df.filter(like="_Rent").T
        
        st.line_chart(rev_data)
        st.line_chart(rent_data)
