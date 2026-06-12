import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.info("Upload your CSV file in the sidebar.")
    st.stop()

@st.cache_data
def load_fixed_data(file):
    # Get the raw headers to know how many months there are
    raw_header = pd.read_csv(file, nrows=0)
    
    # Create unique names: ID, Apr-2023_Cap, Apr-2023_Rent, Apr-2023_Rev, ...
    new_cols = [raw_header.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    
    # Skip the first column (ID) and iterate in steps of 3
    for i in range(1, len(raw_header.columns), 3):
        date = raw_header.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    # Load data using these unique names
    df = pd.read_csv(file, names=new_cols, header=1)
    return df

df = load_fixed_data(uploaded_file)
id_col = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO
with tabs[0]:
    st.subheader("Portfolio Performance")
    # Spatial: Cap * 6
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
    target = st.selectbox("Warehouse:", options=df[id_col].unique())
    slice_df = df[df[id_col] == target]
    
    if not slice_df.empty:
        # Plotting the unique columns we created
        st.write("Revenue Trend")
        st.line_chart(slice_df.filter(like="_Rev").T)
        st.write("Rent Trend")
        st.line_chart(slice_df.filter(like="_Rent").T)
