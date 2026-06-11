import streamlit as st
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Warehouse Analyzer", layout="wide")

# 2. Data Loader
@st.cache_resource
def load_data():
    df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data")
    return df

df_raw = load_data()

# 3. Sidebar (Global Controls)
st.sidebar.title("⚙️ Global Audit Controls")
selected_fy = st.sidebar.selectbox("Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"])

# 4. Skeleton Tabs
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Compare Years", "🔍 Individual Drilldown"])

with tabs[0]:
    st.subheader("Portfolio Summary")
    st.write("Ready to receive calculation logic.")

with tabs[1]:
    st.subheader("YoY Rent Analyzer")
    st.write("Ready to receive seasoned asset logic.")

with tabs[2]:
    st.subheader("Compare Years")
    st.write("Ready to receive dual-year overlay logic.")

with tabs[3]:
    st.subheader("Individual Drilldown")
    st.write("Ready to receive warehouse tracking logic.")
