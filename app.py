import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. Page Configuration
st.set_page_config(page_title="Warehouse Performance Analyzer", layout="wide")

# 2. Data Engine
@st.cache_resource
def load_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    df.columns = [str(c).strip() for c in df.columns]
    df["CMP ID"] = df["CMP ID"].astype(str).str.strip().str.upper()
    df["Type_Clean"] = df["Details"].astype(str).str.strip().str.lower()
    return df

df_raw = load_data()

# 3. Sidebar (Global)
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"])

# 4. Main Tabs
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Two Years", "🔍 Individual Warehouse Drilldown"])

# TAB 0: Portfolio Summary (The Metrics View)
with tabs[0]:
    st.subheader(f"Portfolio Financial Overview - {selected_fy}")
    # We will build the metrics here using df_raw calculations
    st.write("Metric Rows and Clusters bar chart rendering...")

# TAB 1: YoY Rent Analyzer
with tabs[1]:
    st.subheader("YoY Rent Analyzer")
    st.multiselect("Filter Assets:", options=sorted(df_raw["CMP ID"].unique()))
    st.write("Clustered bar graph with PSF logic here.")

# TAB 2: Compare Two Years
with tabs[2]:
    st.subheader("Compare Two Years")
    c1, c2 = st.columns(2)
    c1.selectbox("Baseline Year", ["FY 23-24", "FY 24-25"], key="base")
    c2.selectbox("Target Year", ["FY 24-25", "FY 25-26"], key="target")
    st.write("Overlay Rent vs Revenue PSF charts here.")

# TAB 3: Drilldown
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target_wh = st.selectbox("Facility:", options=sorted(df_raw["CMP ID"].unique()))
    
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    st.write("Chronological sequence graph rendering here.")
