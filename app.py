import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. LOAD & CLEAN DATA
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["csv", "xlsx"])
if not uploaded_file:
    st.info("Upload your file in the sidebar.")
    st.stop()

@st.cache_data
def load_data(file):
    # Read first row to handle the repeating triplets
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    # RENAME COLUMNS: Turn duplicate headers into triplets [Date_Cap, Date_Rent, Date_Rev]
    new_cols = [df.columns[0]]
    triplets = ["Capacity", "Rent", "Rev"]
    col_idx = 1
    while col_idx < len(df.columns):
        date = df.columns[col_idx]
        for t in triplets:
            new_cols.append(f"{date}_{t}")
            col_idx += 1
    df.columns = new_cols
    return df

df = load_data(uploaded_file)
warehouse_id = df.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Spatial Metric: Capacity * 6
    total_mt = df.filter(like="_Capacity").sum().sum()
    st.metric("Total Storage (Sq. Ft.)", f"{total_mt * 6:,.0f} Sq. Ft.")
    st.write("Metric: Capacity (MT) * 6 = Sq. Ft.")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[warehouse_id].unique())
    slice_df = df[df[warehouse_id] == target]
    
    if not slice_df.empty:
        # Plot Revenue and Rent for the selected warehouse
        rev_data = slice_df.filter(like="_Rev").T
        rent_data = slice_df.filter(like="_Rent").T
        st.line_chart(rev_data)
        st.line_chart(rent_data)
