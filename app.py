import streamlit as st
import pandas as pd
import plotly.express as px

# Dashboard Configuration
st.set_page_config(layout="wide", page_title="Warehouse Analytics")

# 1. LOAD DATA
@st.cache_data
def load_data():
    # Reads the file from your GitHub repository
    df = pd.read_csv('Warehouse_Analysis_Cleaned.csv')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

# Initialize Data
try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data file. Please ensure 'Warehouse_Analysis_Cleaned.csv' is in your GitHub repo. Error: {e}")
    st.stop()

# 2. SIDEBAR NAVIGATION
st.sidebar.title("Warehouse Controls")
selected_warehouse = st.sidebar.selectbox("Select Warehouse", df['Warehouse'].unique())

# 3. MAIN DASHBOARD CONTENT
st.title(f"📊 Dashboard: {selected_warehouse}")

# KPIs (Using the latest data point for the selected warehouse)
site_data = df[df['Warehouse'] == selected_warehouse]
latest_rev = site_data[site_data['Metric'] == 'Rev'].iloc[-1]['Value'] if not site_data[site_data['Metric'] == 'Rev'].empty else 0
latest_rent = site_data[site_data['Metric'] == 'Rent'].iloc[-1]['Value'] if not site_data[site_data['Metric'] == 'Rent'].empty else 0
latest_cap = site_data[site_data['Metric'] == 'Cap'].iloc[-1]['Value'] if not site_data[site_data['Metric'] == 'Cap'].empty else 0

c1, c2, c3 = st.columns(3)
c1.metric("Current Revenue", f"₹{latest_rev:,.0f}")
c2.metric("Current Rent", f"₹{latest_rent:,.0f}")
c3.metric("Current Capacity", f"{latest_cap:,.0f} MT")

# CHARTING
st.subheader("Performance Trends")
fig = px.line(
    site_data, 
    x='Date', 
    y='Value', 
    color='Metric', 
    markers=True,
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# RAW DATA VIEW
if st.checkbox("Show Raw Data"):
    st.dataframe(site_data)
