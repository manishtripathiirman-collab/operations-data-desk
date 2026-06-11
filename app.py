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
tab1, tab2, tab3 = st.tabs(["📈 Portfolio Performance Summary", "🔄 YoY Sq. Ft. Rent Analyzer", "🔍 Individual Warehouse Drilldown"])

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
# TAB 2: ADJUSTED PER SQUARE FOOT YoY ANALYZER (Capacity * 6)
# =========================================================================
with tab2:
    st.header("📐 Per Square Foot (PSF) Lease Cost Tracking")
    st.markdown("Isolating warehouses with continuous records to monitor YoY real estate spatial efficiency.")
    
    years = ["FY 23-24", "FY 24-25", "FY 25-26"]
    summary_df = df_raw.groupby(["CMP ID", "Capacity", "Details"])[years].sum().reset_index()
    
    # Isolate stable warehouses with revenue entries across all milestones
    valid_ids = summary_df[
        (summary_df["Details"] == "Rev") & 
        (summary_df["FY 23-24"] > 0) & 
        (summary_df["FY 24-25"] > 0) & 
        (summary_df["FY 25-26"] > 0)
    ]["CMP ID"].unique()
    
    seasoned_rent = summary_df[(summary_df["CMP ID"].isin(valid_ids)) & (summary_df["Details"] == "Rent")].copy()
    
    if not seasoned_rent.empty:
        # UPDATED BASED ON YOUR REQUEST: 1 MT requires exactly 6 Sq. Ft. of footprint layout
        seasoned_rent["Estimated SqFt"] = seasoned_rent["Capacity"] * 6
        
        # Calculate Per Square Foot rent for each individual fiscal year line
        for yr in years:
            seasoned_rent[f"{yr}_PSF"] = seasoned_rent[yr] / seasoned_rent["Estimated SqFt"]
            
        # Melt data cleanly to plot the YoY changes side-by-side
        psf_cols = [f"{yr}_PSF" for yr in years]
        melt_psf = seasoned_rent.melt(
            id_vars=["CMP ID", "Capacity", "Estimated SqFt"],
            value_vars=psf_cols,
            var_name="Fiscal Year",
            value_name="Rent PSF"
        )
        # Simplify names from 'FY 23-24_PSF' to just 'FY 23-24'
        melt_psf["Fiscal Year"] = melt_psf["Fiscal Year"].apply(lambda x: x.split('_')[0])
        
        # Interactive YoY Plot
        fig_psf = px.bar(
            melt_psf,
            x="CMP ID",
            y="Rent PSF",
            color="Fiscal Year",
            barmode="group",
            title="Year-on-Year Rent Cost per Square Foot Comparison (1 MT = 6 Sq. Ft.)",
            labels={"Rent PSF": "Rent per Sq. Ft. (₹)"},
            color_discrete_sequence=px.colors.sequential.Teal
        )
        st.plotly_chart(fig_psf, use_container_width=True)
        
        # Professional Matrix Grid View
        st.subheader("📊 Spatial Efficiency Ledger")
        display_cols = ["CMP ID", "Capacity", "Estimated SqFt", "FY 23-24_PSF", "FY 24-25_PSF", "FY 25-26_PSF"]
        ledger_df = seasoned_rent[display_cols].copy()
        
        st.dataframe(
            ledger_df.style.format({
                "Capacity": "{:,.0f} MT",
                "Estimated SqFt": "{:,.0f} Sq. Ft.",
                "FY 23-24_PSF": "₹{:.2f}/sqft",
                "FY 24-25_PSF": "₹{:.2f}/sqft",
                "FY 25-26_PSF": "₹{:.2f}/sqft"
            }),
            use_container_width=True
        )
    else:
        st.info("No long-term operational facilities found matching continuous multi-year milestones.")

# =========================================================================
# TAB 3: INDIVIDUAL WAREHOUSE DRILLDOWN
# =========================================================================
with tab3:
    st.header("🔍 Granular Asset Investigation Desk")
    
    selected_facility = st.selectbox("Select Target Facility to Inspect", df_raw["CMP ID"].unique())
    facility_profile = df_raw[df_raw["CMP ID"] == selected_facility]
    
    month_cols = [col for col in df_raw.columns if any(year in str(col) for year in ["2023", "2024", "2025", "2026"])]
    
    if not facility_profile.empty and len(month_cols) > 0:
        cap_val = facility_profile["Capacity"].values[0]
        st.metric("Storage Volume Capacity (MT)", f"{cap_val:,} MT")
        
        timeline_df = facility_profile.melt(id_vars=["Details"], value_vars=month_cols, var_name="Month", value_name="Amount")
        timeline_df["Month"] = pd.to_datetime(timeline_df["Month"])
        timeline_df = timeline_df.sort_values("Month")
        
        fig_time = px.line(timeline_df, x="Month", y="Amount", color="Details", markers=True, color_discrete_map={"Rent": "#EF553B", "Rev": "#00CC96"})
        st.plotly_chart(fig_time, use_container_width=True)
