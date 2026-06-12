import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.info("Please upload your CSV file.")
    st.stop()

@st.cache_data
def load_and_fix(file):
    # Read the first two rows to determine structure
    header_row = pd.read_csv(file, nrows=0)
    # Your file has repeating column names. We assign unique names: 
    # [CMP ID, Cap1, Rent1, Rev1, Cap2, Rent2, Rev2...]
    cols = ['CMP ID']
    for i in range((len(header_row.columns) - 1) // 3):
        cols.extend([f"Cap_{i}", f"Rent_{i}", f"Rev_{i}"])
    
    df = pd.read_csv(file, names=cols, header=1)
    return df

df = load_and_fix(uploaded_file)

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO
with tabs[0]:
    st.subheader("Portfolio Performance")
    # Total Calculation
    total_rev = df.filter(like="Rev").sum().sum()
    total_rent = df.filter(like="Rent").sum().sum()
    total_cap = df.filter(like="Cap").sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area (SqFt)", f"{(total_cap * 6):,.0f}")

# TAB 4: DRILLDOWN
with tabs[3]:
    target = st.selectbox("Warehouse:", options=df["CMP ID"].unique())
    slice_df = df[df["CMP ID"] == target]
    
    if not slice_df.empty:
        # Get Rev and Rent rows
        rev_data = slice_df.filter(like="Rev").values.flatten()
        rent_data = slice_df.filter(like="Rent").values.flatten()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=rev_data, name="Revenue"))
        fig.add_trace(go.Scatter(y=rent_data, name="Rent"))
        st.plotly_chart(fig, use_container_width=True)
