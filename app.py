import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload 'Warehouse_Analysis_Wide_Format.xlsx'", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Upload your Excel file to begin.")
    st.stop()

@st.cache_data
def load_data(file):
    df = pd.read_excel(file) if file.name.endswith(".xlsx") else pd.read_csv(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_data(uploaded_file)
warehouse_col = df.columns[0] # Usually 'Warehouse'

# Helper to identify column types (Capacity, Rent, Rev)
def get_cols(type_str):
    return [c for c in df.columns if type_str in c]

tabs = st.tabs(["📈 Portfolio Performance", "🔄 YoY Rent Analyzer", "📊 Compare Two Years", "🔍 Warehouse Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Logic: Sum everything for current selection
    total_rev = df[get_cols("Rev")].sum().sum()
    total_rent = df[get_cols("Rent")].sum().sum()
    total_cap = df[get_cols("Capacity")].sum().sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    col2.metric("Total Rent", f"₹{total_rent:,.0f}")
    col3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    col4.metric("Efficiency", f"{(total_rent/total_rev)*100:.1f}%" if total_rev > 0 else "0%")

# TAB 2: YoY RENT ANALYZER
with tabs[2]: # Simplified logic for comparison
    st.subheader("Two-Year Comparison")
    y1, y2 = st.columns(2)
    yr1 = y1.selectbox("Baseline Year", ["2023", "2024", "2025"])
    yr2 = y2.selectbox("Target Year", ["2024", "2025", "2026"])
    
    if yr1 == yr2:
        st.warning("Please select different years.")
    else:
        # PSF Math: (Rent / (Capacity * 6))
        fig = go.Figure()
        # You will add your data mapping here
        st.write(f"Comparing {yr1} and {yr2} performance spreads.")

# TAB 4: DRILLDOWN
with tabs[3]:
    target = st.selectbox("Select Warehouse:", df[warehouse_col].unique())
    wh_slice = df[df[warehouse_col] == target]
    
    if not wh_slice.empty:
        # Create a clean timeline for Revenue vs Rent
        st.line_chart(wh_slice.filter(like="Rev").T)
        st.line_chart(wh_slice.filter(like="Rent").T)
