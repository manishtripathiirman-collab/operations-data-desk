import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Warehouse Dashboard")

# 1. FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Excel File", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload your .xlsx file in the sidebar to begin.")
    st.stop()

@st.cache_data
def load_and_clean_data(file):
    # Read headers to understand structure
    header_df = pd.read_excel(file, nrows=0)
    
    # Generate unique names
    new_cols = [header_df.columns[0]]
    triplets = ["_Cap", "_Rent", "_Rev"]
    for i in range(1, len(header_df.columns), 3):
        date = header_df.columns[i]
        for t in triplets:
            new_cols.append(f"{date}{t}")
            
    df = pd.read_excel(file, header=1, names=new_cols)
    
    # Convert to Long Format (Tidy)
    df_long = df.melt(id_vars=[df.columns[0]], var_name="Date_Metric", value_name="Value")
    
    # Split column into Date and Metric
    df_long[['Date', 'Metric']] = df_long['Date_Metric'].str.extract(r'(.*)_(.*)')
    df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')
    df_long = df_long.drop(columns=['Date_Metric'])
    
    return df_long

df_long = load_and_clean_data(uploaded_file)
warehouse_col = df_long.columns[0]

# 2. TABS
tabs = st.tabs(["📈 Portfolio", "🔄 YoY Rent", "📊 Compare", "🔍 Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    pivot_df = df_long.groupby('Metric')['Value'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{pivot_df.get('Rev', 0):,.0f}")
    c2.metric("Total Rent", f"₹{pivot_df.get('Rent', 0):,.0f}")
    c3.metric("Net Surplus", f"₹{pivot_df.get('Rev', 0) - pivot_df.get('Rent', 0):,.0f}")
    c4.metric("Total Capacity", f"{pivot_df.get('Cap', 0):,.0f} MT")

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Warehouse Drilldown")
    target = st.selectbox("Select Warehouse:", options=df_long[warehouse_col].unique())
    slice_df = df_long[df_long[warehouse_col] == target]
    
    # Create interactive Plotly charts
    for metric in ['Rev', 'Rent', 'Cap']:
        fig = px.line(
            slice_df[slice_df['Metric'] == metric], 
            x='Date', y='Value', 
            title=f"{metric} Trend",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
