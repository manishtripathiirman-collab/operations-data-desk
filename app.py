import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# 1. FILE UPLOADER - EXCEL ONLY
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Excel File", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload your .xlsx file in the sidebar.")
    st.stop()

@st.cache_data
def load_and_fix_excel(file):
    # Load raw header to rename duplicate columns
    header_df = pd.read_excel(file, nrows=0)
    
    # Generate unique names: ID, Date_Cap, Date_Rent, Date_Rev...
    new_cols = [header_df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    
    # Iterate through the triplets (assuming 3 columns per month)
    for i in range(1, len(header_df.columns), 3):
        date = header_df.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    # Load data using the newly generated unique names
    df = pd.read_excel(file, header=1, names=new_cols)
    return df

df = load_and_fix_excel(uploaded_file)
warehouse_id = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Spatial: Capacity (MT) * 6 = Sq. Ft.
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
    target = st.selectbox("Select Warehouse:", options=df[warehouse_id].unique())
    slice_df = df[df[warehouse_id] == target]
    
    # Plotting Trends
    st.write("Revenue Trends")
    st.line_chart(slice_df.filter(like="_Rev").T)
    st.write("Rent Trends")
    st.line_chart(slice_df.filter(like="_Rent").T)
