import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. PAGE LAYOUT CONFIGURATION
st.set_page_config(layout="wide", page_title="Operations Data Desk")

st.title("🏢 Warehouse Performance Portal")
st.markdown("Track rent costs, revenue streams, and asset efficiency across multi-year milestones.")
st.markdown("---")

# 2. LOAD DATA DIRECTLY FROM YOUR EXCEL WORKBOOK (.XLSX)
@st.cache_data
def load_excel_data():
    raw_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data", engine="openpyxl")
    # Clean string spaces from your main identifier columns immediately
    raw_df["CMP ID"] = raw_df["CMP ID"].astype(str).str.strip()
    raw_df["Details"] = raw_df["Details"].astype(str).str.strip()
    
    rent_details_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="Rent Data", skiprows=1, engine="openpyxl")
    return raw_df, rent_details_df

try:
    df_raw, df_rent_details = load_excel_data()
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
    st.stop()

# 3. GLOBAL CONTROL FILTERS (SIDEBAR)
st.sidebar.header("🎛️ Page Filters")
selected_fy = st.sidebar.selectbox("Select Target Fiscal Year (Tab 1 & 2)", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)

min_cap = int(df_raw["Capacity"].min())
max_cap = int(df_raw["Capacity"].max())
selected_capacity = st.sidebar.slider("Filter by Warehouse Capacity (MT)", min_cap, max_cap, (min_cap, max_cap))

# Apply baseline filtering based on sidebar selections
df_filtered_raw = df_raw[
    (df_raw["Capacity"] >= selected_capacity[0]) & 
    (df_raw["Capacity"] <= selected_capacity[1])
]

# SAFE UNDER-THE-HOOD DATA INSPECTOR (In Sidebar to find why values are 0)
st.sidebar.markdown("---")
with st.sidebar.expander("🔍 Inspect Hidden Excel Formatting"):
    st.write("**Exact labels found in Details column:**")
    st.code(list(df_raw["Details"].unique()))
    st.write("**Data types of your Year Columns:**")
    st.write(f"FY 23-24 type: {df_raw['FY 23-24'].dtype}")
    st.write(f"FY 24-25 type: {df_raw['FY 24-25'].dtype}")
    st.write(f"FY 25-26 type: {df_raw['FY 25-26'].dtype}")
    st.write("**First 3 rows of raw file data:**")
    st.dataframe(df_raw[["CMP ID", "Details", "FY 23-24"]].head(3))

# 4. TABBED LAYOUT CREATION
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Portfolio Performance Summary", 
    "🔄 YoY Sq. Ft. Rent Analyzer", 
    "📊 Compare Two Years", 
    "🔍 Individual Warehouse Drilldown"
])

# =========================================================================
# TAB 1: PORTFOLIO SUMMARY
# =========================================================================
with tab1:
    st.header("📌 Macro Financial & Spatial Summary")
    
    total_rent = df_filtered_raw[df_filtered_raw["Details"] == "Rent"][selected_fy].sum()
    total_rev = df_filtered_raw[df_filtered_raw["Details"] == "Rev"][selected_fy].sum()
    net_surplus = total_rev - total_rent
    rent_to_rev_ratio = (total_rent / total_rev * 100) if total_rev > 0 else 0
    
    total_capacity_mt = df_filtered_raw.drop_duplicates(subset=["CMP ID"])["Capacity"].sum()
    total_sqft_leased = total_capacity_mt * 6
    
    rev_per_sqft = (total_rev / total_sqft_leased) if total_sqft_leased > 0 else 0
    rent_per_sqft = (total_rent / total_sqft_leased) if total_sqft_leased > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 Total Portfolio Revenue", f"₹{total_rev:,.0f}")
    m2.metric("📉 Total Fixed Rent Costs", f"₹{total_rent:,.0f}")
    m3.metric("🏛️ Net Contribution Surplus", f"₹{net_surplus:,.0f}")
    m4.metric("📊 Rent-to-Revenue Efficiency", f"{rent_to_rev_ratio:.1f}%")
    
    st.markdown("#### 📐 Spatial Unit Rate Performance Metrics")
    s1, s2, s3 = st.columns(3)
    s1.metric("🏢 Total Area Leased (Footprint)", f"{total_sqft_leased:,.0f} Sq. Ft.")
    s2.metric("🟢 Macro Revenue / Sq. Ft.", f"₹{rev_per_sqft:.2f}/sqft")
    s3.metric("🔴 Macro Rent / Sq. Ft.", f"₹{rent_per_sqft:.2f}/sqft")
    
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🏆 Top 10 Revenue Generating Clusters")
        top_rev = df_filtered_raw[df_filtered_raw["Details"] == "Rev"].nlargest(10, selected_fy)
        fig_bar = px.bar(top_rev, x=selected_fy, y="CMP ID", orientation='h', color=selected_fy, color_continuous_scale="Viridis")
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with chart_col2:
        st.subheader("🎯 Overhead Efficiency Scatter Profiler")
        pivoted = df_filtered_raw.pivot_table(index=["CMP ID", "Capacity"], columns="Details", values=selected_fy).reset_index()
        if "Rent" in pivoted.columns and "Rev" in pivoted.columns:
            fig_scatter = px.scatter(pivoted, x="Rent", y="Rev", size="Capacity", hover_name="CMP ID", color="Rev", color_continuous_scale="RdYlGn", trendline="ols")
            st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================================
# TAB 2: PER SQUARE FOOT YoY ANALYZER (Warehouses > 2 Years)
# =================================
