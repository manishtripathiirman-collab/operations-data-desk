import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.info("Upload your CSV file in the sidebar.")
    st.stop()

@st.cache_data
def load_and_fix(file):
    # Read the file
    df = pd.read_csv(file)
    
    # RENAME: Force unique names for the repeating triplets
    # We take the first column as CMP ID, then assume triplets for the rest
    new_cols = [df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    
    # Build a new list of column names
    for i in range(1, len(df.columns), 3):
        date = df.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    df.columns = new_cols
    return df

df = load_and_fix(uploaded_file)
id_col = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Spatial Calculation: MT * 6 = Sq Ft
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
    st.subheader("Individual Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[id_col].unique())
    slice_df = df[df[id_col] == target]
    
    if not slice_df.empty:
        # Plotting specific columns
        st.line_chart(slice_df.filter(like="_Rev").T)
        st.line_chart(slice_df.filter(like="_Rent").T)
