import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PAGE LAYOUT CONFIGURATION
st.set_page_config(layout="wide", page_title="Operations Data Desk")

st.title("🏢 Warehouse Performance Portal")
st.markdown("Track rent costs, revenue streams, and asset efficiency below across multi-year milestones.")
st.markdown("---")

# 2. LOAD DATA DIRECTLY FROM YOUR EXCEL WORKBOOK (.XLSX)
@st.cache_data
def load_excel_data():
    raw_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data", engine="openpyxl")
    rent_details_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="Rent Data", engine="openpyxl")
    return raw_df, rent_details_df

try:
    df_raw, df_rent_details = load_excel_data()
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
    st.stop()

# 3. GLOBAL CONTROL FILTERS (SIDEBAR)
st.sidebar.header("🎛️ Page Filters")
selected_fy = st.sidebar.selectbox("Select Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)

# Set slider range dynamically based on your data's capacity sizes
min_cap = int(df_raw["Capacity"].min())
max_cap = int(df_raw["Capacity"].max())
selected_capacity = st.sidebar.slider("Filter by Warehouse Capacity (MT)", min_cap, max_cap, (min_cap, max_cap))

# Apply baseline filtering based on the capacity slider
df_filtered_raw = df_raw[
    (df_raw["Capacity"] >= selected_capacity[0]) & 
    (df_raw["Capacity"] <= selected_capacity[1])
]

# 4. TABBED LAYOUT CREATION
tab1, tab2, tab3 = st.tabs(["📈 Portfolio Performance Summary", "🗺️ Regional Demographics", "🔍 Individual Warehouse Drilldown"])

# =========================================================================
# TAB 1: PORTFOLIO SUMMARY (Fully functional and safe)
# =========================================================================
with tab1:
    st.header("📌 Macro Financial Summary")
    
    # Isolate Rent and Revenue to calculate summary statistics
    total_rent = df_filtered_raw[df_filtered_raw["Details"] == "Rent"][selected_fy].sum()
    total_rev = df_filtered_raw[df_filtered_raw["Details"] == "Rev"][selected_fy].sum()
    net_surplus = total_rev - total_rent
    rent_to_rev_ratio = (total_rent / total_rev * 100) if total_rev > 0 else 0
    
    # Display performance indicators
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 Total Portfolio Revenue", f"₹{total_rev:,.0f}")
    m2.metric("📉 Total Fixed Rent Costs", f"₹{total_rent:,.0f}")
    m3.metric("🏛️ Net Contribution Surplus", f"₹{net_surplus:,.0f}")
    m4.metric("📊 Rent-to-Revenue Efficiency", f"{rent_to_rev_ratio:.1f}%")
    
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🏆 Top 10 Revenue Generating Clusters")
        top_rev = df_filtered_raw[df_filtered_raw["Details"] == "Rev"].nlargest(10, selected_fy)
        fig_bar = px.bar(top_rev, x=selected_fy, y="CMP ID", orientation='h', color=selected_fy, color_continuous_scale="Viridis")
        fig_bar.update_layout(yaxis={'width': 'stretch'}, showlegend=False)
        st.plotly_chart(fig_bar, width="stretch")
        
    with chart_col2:
        st.subheader("🎯 Overhead Efficiency Scatter Profiler")
        pivoted = df_filtered_raw.pivot_table(index=["CMP ID", "Capacity"], columns="Details", values=selected_fy).reset_index()
        if "Rent" in pivoted.columns and "Rev" in pivoted.columns:
            fig_scatter = px.scatter(pivoted, x="Rent", y="Rev", size="Capacity", hover_name="CMP ID", color="Rev", color_continuous_scale="RdYlGn", trendline="ols")
            st.plotly_chart(fig_scatter, width="stretch")

# =========================================================================
# TAB 2: REGIONAL DEMOGRAPHICS (Protected from crashes)
# =========================================================================
with tab2:
    st.header("🗺️ Regional State Performance")
    st.info("Let's align your Rent Data sheet column layout. Here is a preview of what the raw sheet looks like:")
    # Shows you the top 5 rows of your sheet so we can find where State Name and CMP Name live
    st.dataframe(df_rent_details.head(5))

# =========================================================================
# TAB 3: INDIVIDUAL WAREHOUSE DRILLDOWN (Safe timeline rendering)
# =========================================================================
with tab3:
    st.header("🔍 Granular Asset Investigation Desk")
    
    selected_facility = st.selectbox("Select Target Facility to Inspect", df_raw["CMP ID"].unique())
    facility_profile = df_raw[df_raw["CMP ID"] == selected_facility]
    
    # Grab the date/monthly snapshot columns present in your file safely
    month_cols = [col for col in df_raw.columns if any(year in str(col) for year in ["2023", "2024", "2025", "2026"])]
    
    if not facility_profile.empty and len(month_cols) > 0:
        cap_val = facility_profile["Capacity"].values[0]
        st.metric("Storage Volume Capacity (MT)", f"{cap_val:,} MT")
        
        # Reshape data to plot timeline
        timeline_df = facility_profile.melt(id_vars=["Details"], value_vars=month_cols, var_name="Month", value_name="Amount")
        timeline_df["Month"] = pd.to_datetime(timeline_df["Month"])
        timeline_df = timeline_df.sort_values("Month")
        
        fig_time = px.line(timeline_df, x="Month", y="Amount", color="Details", markers=True, color_discrete_map={"Rent": "#EF553B", "Rev": "#00CC96"})
        st.plotly_chart(fig_time, width="stretch")
