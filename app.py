import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. FILE LOADER
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.info("Upload your CSV file in the sidebar.")
    st.stop()

@st.cache_data
def load_and_fix(file):
    # Read headers to rename them
    header_df = pd.read_csv(file, nrows=0)
    
    # Generate unique names: ID, Apr-2023_Cap, Apr-2023_Rent, Apr-2023_Rev, ...
    new_cols = [header_df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    
    # Iterate through the triplet pattern in your CSV
    for i in range(1, len(header_df.columns), 3):
        date = header_df.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    df = pd.read_csv(file, names=new_cols, header=1)
    return df

df = load_and_fix(uploaded_file)
id_col = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO
with tabs[0]:
    st.subheader("Portfolio Performance")
    # Spatial: sum all capacity columns * 6
    total_mt = df.filter(like="_Cap").sum().sum()
    total_rev = df.filter(like="_Rev").sum().sum()
    total_rent = df.filter(like="_Rent").sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area (SqFt)", f"{total_mt * 6:,.0f}")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[id_col].unique())
    slice_df = df[df[id_col] == target]
    
    if not slice_df.empty:
        # Separate Rev and Rent
        rev_df = slice_df.filter(like="_Rev").T
        rent_df = slice_df.filter(like="_Rent").T
        
        st.write("Revenue Trend")
        st.line_chart(rev_df)
        st.write("Rent Trend")
        st.line_chart(rent_df)
