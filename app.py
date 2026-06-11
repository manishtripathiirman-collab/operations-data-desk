import streamlit as st
import pandas as pd
import plotly.express as px

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
selected_fy = st.sidebar.selectbox("Select Target Fiscal Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)

min_cap = int(df_raw["Capacity"].min())
max_cap = int(df_raw["Capacity"].max())
selected_capacity = st.sidebar.slider("Filter by Warehouse Capacity (MT)", min_cap, max_cap, (min_cap, max_cap))

# Apply baseline filtering based on sidebar selections
df_filtered_raw = df_raw[
    (df_raw["Capacity"] >= selected_capacity[0]) & 
    (df_raw["Capacity"] <= selected_capacity[1])
]

# 4. TABBED LAYOUT CREATION
tab1, tab2, tab3 = st.tabs(["📈 Portfolio Performance Summary", "🔄 Year-on-Year (YoY) Analyzer", "🔍 Individual Warehouse Drilldown"])

# =========================================================================
# TAB 1: PORTFOLIO SUMMARY
# =========================================================================
with tab1:
    st.header("📌 Macro Financial Summary")
    
    total_rent = df_filtered_raw[df_filtered_raw["Details"] == "Rent"][selected_fy].sum()
    total_rev = df_filtered_raw[df_filtered_raw["Details"] == "Rev"][selected_fy].sum()
    net_surplus = total_rev - total_rent
    rent_to_rev_ratio = (total_rent / total_rev * 100) if total_rev > 0 else 0
    
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
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with chart_col2:
        st.subheader("🎯 Overhead Efficiency Scatter Profiler")
        pivoted = df_filtered_raw.pivot_table(index=["CMP ID", "Capacity"], columns="Details", values=selected_fy).reset_index()
        if "Rent" in pivoted.columns and "Rev" in pivoted.columns:
            fig_scatter = px.scatter(pivoted, x="Rent", y="Rev", size="Capacity", hover_name="CMP ID", color="Rev", color_continuous_scale="RdYlGn", trendline="ols")
            st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================================
# TAB 2: YoY MULTI-YEAR ANALYZER (No Pivot, No KeyErrors)
# =========================================================================
with tab2:
    st.header("🔄 Multi-Year Performance Comparison")
    st.markdown("Showing warehouses with full operational records stretching over multiple fiscal periods.")
    
    # Isolate active warehouses present across all 3 primary years from the source data
    years = ["FY 23-24", "FY 24-25", "FY 25-26"]
    
    # Group raw data to get clean individual rows for each warehouse and its details
    summary_df = df_raw.groupby(["CMP ID", "Capacity", "Details"])[years].sum().reset_index()
    
    # Find list of unique CMP IDs that have positive revenue in all 3 target years
    rev_mask = summary_df["Details"] == "Rev"
    valid_ids = summary_df[
        rev_mask & 
        (summary_df["FY 23-24"] > 0) & 
        (summary_df["FY 24-25"] > 0) & 
        (summary_df["FY 25-26"] > 0)
    ]["CMP ID"].unique()
    
    # Filter the dataframe to only keep these stable, multi-year warehouses
    seasoned_data = summary_df[summary_df["CMP ID"].isin(valid_ids)].copy()
    
    if len(seasoned_data) > 0:
        # User selection toggle
        target_view = st.radio("Choose Comparison Metric", ["Revenue Grouping", "Rent Cost Grouping"], horizontal=True)
        mapped_detail = "Rev" if "Revenue" in target_view else "Rent"
        
        # Filter for the chart visualization
        chart_df = seasoned_data[seasoned_data["Details"] == mapped_detail]
        
        # Melt to format data for grouping bars side by side by year
        chart_melt = chart_df.melt(
            id_vars=["CMP ID", "Capacity"], 
            value_vars=years, 
            var_name="Fiscal Year", 
            value_name="Value"
        )
        
        fig_yoy = px.bar(
            chart_melt, 
            x="CMP ID", 
            y="Value", 
            color="Fiscal Year", 
            barmode="group",
            title=f"Year-over-Year {mapped_detail} Growth Matrix",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_yoy, use_container_width=True)
        
        # Render a clean spreadsheet ledger underneath
        st.subheader("📊 Performance Ledger")
        
        # Format a flat spreadsheet for simple operational reading
        flat_ledger = chart_df.rename(columns={
            "FY 23-24": f"FY 23-24 ({mapped_detail})",
            "FY 24-25": f"FY 24-25 ({mapped_detail})",
            "FY 25-26":
