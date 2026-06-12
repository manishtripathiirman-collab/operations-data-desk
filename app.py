import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload your CSV", type=["csv", "xlsx"])
if not uploaded_file:
    st.info("Upload your file to begin.")
    st.stop()

@st.cache_data
def load_and_prep(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_and_prep(uploaded_file)
warehouse_col = df.columns[0]

# 2. DYNAMIC CATEGORY FINDER
def get_cols(keyword):
    # Returns columns that contain the keyword (e.g., 'Rev', 'Rent', 'Capacity')
    return [c for c in df.columns if keyword.lower() in c.lower()]

# 3. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Use keywords to sum everything
    rev_cols = get_cols("Rev")
    rent_cols = get_cols("Rent")
    cap_cols = get_cols("Capacity")
    
    total_rev = df[rev_cols].sum().sum()
    total_rent = df[rent_cols].sum().sum()
    total_mt = df[cap_cols].sum().sum()
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Total Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area", f"{total_mt * 6:,.0f} Sq. Ft.")

with tabs[3]:
    st.subheader("Individual Drilldown")
    target = st.selectbox("Select Warehouse:", options=df[warehouse_col].unique())
    slice_df = df[df[warehouse_col] == target].copy()
    
    # Melt the data so we can chart it
    melted = slice_df.melt(id_vars=[warehouse_col])
    # Simple line chart
    st.line_chart(melted, x="variable", y="value")
