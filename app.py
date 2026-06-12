import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. SIDEBAR UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data", type=["csv"])
if not uploaded_file:
    st.info("Upload your CSV file to begin.")
    st.stop()

@st.cache_data
def load_and_fix(file):
    # Read raw header
    raw_df = pd.read_csv(file)
    
    # RENAME: Force unique names for the repeating triplets
    # Format: ID, Date_Cap, Date_Rent, Date_Rev...
    new_cols = [raw_df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    
    # Iterate in steps of 3 to rename all columns properly
    for i in range(1, len(raw_df.columns), 3):
        date = raw_df.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    # Apply new headers
    df = pd.read_csv(file, names=new_cols, header=1)
    return df

df = load_and_fix(uploaded_file)
wh_col = df.columns[0]

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
    c1.metric("Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area", f"{total_mt * 6:,.0f} Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    target = st.selectbox("Warehouse:", options=df[wh_col].unique())
    slice_df = df[df[wh_col] == target]
    
    if not slice_df.empty:
        # Plotting the unique columns we created
        st.write("Revenue History")
        st.line_chart(slice_df.filter(like="_Rev").T)
        st.write("Rent History")
        st.line_chart(slice_df.filter(like="_Rent").T)
