import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

# 1. Page Config
st.set_page_config(page_title="Warehouse Analyzer", layout="wide")

# 2. Data Loader
@st.cache_resource
def load_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    return df

df_raw = load_data()

# 3. Sidebar (Always present)
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"])

# 4. Tabs
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Individual Drilldown"])

# TAB 3: Drilldown (Testing this first to verify functionality)
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    options = sorted(df_raw["CMP ID"].unique().tolist())
    target_wh = st.selectbox("Select Facility:", options=options)
    
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    
    if not wh_slice.empty:
        st.write(f"Displaying sequence for: {target_wh}")
        # Placeholder for your graph logic
        st.line_chart(wh_slice.filter(like="202")) 
    else:
        st.warning("No data found for this asset.")

# 5. Placeholder for other tabs to prevent crashing
with tabs[0]: st.write("Portfolio Summary Logic Pending.")
with tabs[1]: st.write("YoY Analyzer Logic Pending.")
with tabs[2]: st.write("Compare Years Logic Pending.")
