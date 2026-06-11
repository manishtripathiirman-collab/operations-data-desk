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
    
    # Clean text values immediately upon loading
    raw_df["CMP ID"] = raw_df["CMP ID"].astype(str).str.strip().str.upper()
    raw_df["Details"] = raw_df["Details"].astype(str).str.strip()
    
    # Force financial pillars to clean numeric floats on load
    years = ["FY 23-24", "FY 24-25", "FY 25-26"]
    for yr in years:
        if yr in raw_df.columns:
            raw_df[yr] = pd.to_numeric(raw_df[yr], errors='coerce').fillna(0)
            
    rent_df = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="Rent Data", skiprows=1, engine="openpyxl")
    return raw_df, rent_df

try:
    df_raw, df_rent_details = load_excel_data()
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
    st.stop()

# 3. GLOBAL CONTROL FILTERS (SIDEBAR)
st.sidebar.header("🎛️ Page Filters")
selected_fy = st.sidebar.selectbox("Select Target Fiscal Year (Tab 1)", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)

min_cap = int(df_raw["Capacity"].min())
max_cap = int(df_raw["Capacity"].max())
selected_capacity = st.sidebar.slider("Filter by Warehouse Capacity (MT)", min_cap, max_cap, (min_cap, max_cap))

# Tab 1 baseline filter layout assignment
df_filtered_raw = df_raw[
    (df_raw["Capacity"] >= selected_capacity[0]) & 
    (df_raw["Capacity"] <= selected_capacity[1])
]

# 4. TABBED LAYOUT CREATION
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Portfolio Performance Summary", 
    "🔄 YoY Sq. Ft. Rent Analyzer", 
    "📊 Compare Two Years", 
    "🔍 Individual Warehouse Drilldown"
])

# =========================================================================
# TAB 1: PORTFOLIO SUMMARY (Fixed cut-off layout bug)
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
    s1.metric("🏢 Total Area Leased", f"{total_sqft_leased:,.0f} Sq. Ft.")
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
# TAB 2: YoY SQ FT RENT ANALYZER (Bypasses slider constraint)
# =========================================================================
with tab2:
    st.header("📐 Per Square Foot (PSF) Lease Cost Tracking")
    st.markdown("Monitor YoY real estate spatial efficiency for assets active for at least two years.")
    
    years = ["FY 23-24", "FY 24-25", "FY 25-26"]
    summary_df = df_raw.groupby(["CMP ID", "Capacity", "Details"])[years].sum().reset_index()
    
    # Calculate operational depth based on row activity presence
    summary_df["Active_Count"] = (summary_df["FY 23-24"] > 0).astype(int) + (summary_df["FY 24-25"] > 0).astype(int) + (summary_df["FY 25-26"] > 0).astype(int)
    seasoned_ids = summary_df[summary_df["Active_Count"] >= 2]["CMP ID"].unique()
    
    seasoned_rent = summary_df[(summary_df["CMP ID"].isin(seasoned_ids)) & (summary_df["Details"] == "Rent")].copy()
    
    if not seasoned_rent.empty:
        seasoned_rent["Estimated SqFt"] = seasoned_rent["Capacity"] * 6
        for yr in years:
            seasoned_rent[f"{yr}_PSF"] = seasoned_rent[yr] / seasoned_rent["Estimated SqFt"]
            
        selected_warehouses = st.multiselect(
            "🔍 Search and Select Specific Warehouses to Display (Leave blank to see all matched assets):",
            options=sorted(list(seasoned_rent["CMP ID"].unique())),
            placeholder="Type name here..."
        )
            
        display_rent_df = seasoned_rent[seasoned_rent["CMP ID"].isin(selected_warehouses)].copy() if selected_warehouses else seasoned_rent.copy()
            
        melt_psf = display_rent_df.melt(
            id_vars=["CMP ID", "Capacity", "Estimated SqFt"],
            value_vars=[f"{yr}_PSF" for yr in years],
            var_name="Fiscal Year", value_name="Rent PSF"
        )
        melt_psf["Fiscal Year"] = melt_psf["Fiscal Year"].apply(lambda x: x.split('_')[0])
        
        color_map = {"FY 23-24": "#2CA02C", "FY 24-25": "#FFD700", "FY 25-26": "#D62728"}
        
        fig_psf = px.bar(
            melt_psf, x="CMP ID", y="Rent PSF", color="Fiscal Year", barmode="group",
            title="Year-on-Year Rent Cost per Square Foot Comparison (1 MT = 6 Sq. Ft.)",
            labels={"Rent PSF": "Rent per Sq. Ft. (₹)", "CMP ID": "Warehouse Code"},
            color_discrete_map=color_map
        )
        st.plotly_chart(fig_psf, use_container_width=True)
        
        st.subheader("📊 Spatial Efficiency Ledger")
        ledger_df = display_rent_df[["CMP ID", "Capacity", "Estimated SqFt", "FY 23-24_PSF", "FY 24-25_PSF", "FY 25-26_PSF"]].copy()
        fmt = {"Capacity": "{:,.0f} MT", "Estimated SqFt": "{:,.0f} Sq. Ft.", "FY 23-24_PSF": "₹{:.2f}/sf", "FY 24-25_PSF": "₹{:.2f}/sf", "FY 25-26_PSF": "₹{:.2f}/sf"}
        st.dataframe(ledger_df.style.format(fmt), use_container_width=True)
    else:
        st.info("No facilities matching historical search depth benchmarks yet.")

# =========================================================================
# TAB 3: DUAL-YEAR COMPARE TWO YEARS
# =========================================================================
with tab3:
    st.header("📊 Comparative Dual-Period Unit Assessment")
    st.markdown("Isolate and evaluate pricing efficiency dynamics across any two chosen operational horizons.")
    
    c1, c2 = st.columns(2)
    with c1:
        base_year = st.selectbox("Select Baseline Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=0)
    with c2:
        comp_year = st.selectbox("Select Comparison Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=2)
        
    if base_year == comp_year:
        st.warning("Please choose two different fiscal periods to cross-examine comparative parameters.")
    else:
        target_years = [base_year, comp_year]
        paired_summary = df_raw.groupby(["CMP ID", "Capacity", "Details"])[target_years].sum().reset_index()
        
        active_mask = (paired_summary["Details"] == "Rev") & ((paired_summary[base_year] > 0) | (paired_summary[comp_year] > 0))
        paired_valid_ids = paired_summary[active_mask]["CMP ID"].unique()
        paired_seasoned = paired_summary[paired_summary["CMP ID"].isin(paired_valid_ids)].copy()
        
        if not paired_seasoned.empty:
            paired_seasoned["SqFt"] = paired_seasoned["Capacity"] * 6
            comp_pivot = paired_seasoned.pivot_table(index=["CMP ID", "SqFt"], columns="Details", values=[base_year, comp_year]).reset_index()
            
            for col_prefix in [base_year, comp_year]:
                if (col_prefix, "Rev") not in comp_pivot.columns: comp_pivot[(col_prefix, "Rev")] = 0
                if (col_prefix, "Rent") not in comp_pivot.columns: comp_pivot[(col_prefix, "Rent")] = 0
                
            comp_pivot[f"{base_year}_Rev_PSF"] = comp_pivot[(base_year, "Rev")] / comp_pivot["SqFt"]
            comp_pivot[f"{base_year}_Rent_PSF"] = comp_pivot[(base_year, "Rent")] / comp_pivot["SqFt"]
            comp_pivot[f"{comp_year}_Rev_PSF"] = comp_pivot[(comp_year, "Rev")] / comp_pivot["SqFt"]
            comp_pivot[f"{comp_year}_Rent_PSF"] = comp_pivot[(comp_year, "Rent")] / comp_pivot["SqFt"]
            
            selected_compare_warehouses = st.multiselect(
                "🔍 Filter Comparison Visualizer by Facility Code:",
                options=sorted(list(comp_pivot["CMP ID"].unique())), key="tab3_filter"
            )
            
            comp_plot_pivot = comp_pivot[comp_pivot["CMP ID"].isin(selected_compare_warehouses)].copy() if selected_compare_warehouses else comp_pivot.copy()
                
            st.subheader(f"📈 Unit Rate Spread Profile ({base_year} vs {comp_year})")
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(x=comp_plot_pivot["CMP ID"], y=comp_plot_pivot[f"{base_year}_Rev_PSF"], name=f"{base_year} Rev/SqFt", marker_color="#00CC96", offsetgroup=1))
            fig_compare.add_trace(go.Bar(x=comp_plot_pivot["CMP ID"], y=comp_plot_pivot[f"{base_year}_Rent_PSF"], name=f"{base_year} Rent/SqFt", marker_color="#EF553B", offsetgroup=1, base=0, width=0.2))
            fig_compare.add_trace(go.Bar(x=comp_plot_pivot["CMP ID"], y=comp_plot_pivot[f"{comp_year}_Rev_PSF"], name=f"{comp_year} Rev/SqFt", marker_color="#0068C9", offsetgroup=2))
            fig_compare.add_trace(go.Bar(x=comp_plot_pivot["CMP ID"], y=comp_plot_pivot[f"{comp_year}_Rent_PSF"], name=f"{comp_year} Rent/SqFt", marker_color="#FF4B4B", offsetgroup=2, base=0, width=0.2))
            
            fig_compare.update_layout(barmode="group", xaxis_title="Warehouse Code", yaxis_title="Value (₹/Sq. Ft.)", legend_orientation="h")
            st.plotly_chart(fig_compare, use_container_width=True)
            
            st.subheader("📋 Comparative Unit Pricing Matrix")
            ledger_display = pd.DataFrame({
                "CMP ID": comp_pivot["CMP ID"], "Total Area": comp_pivot["SqFt"],
                f"{base_year} Rev/PSF": comp_pivot[f"{base_year}_Rev_PSF"], f"{base_year} Rent/PSF": comp_pivot[f"{base_year}_Rent_PSF"],
                f"{comp_year} Rev/PSF": comp_pivot[f"{comp_year}_Rev_PSF"], f"{comp_year} Rent/PSF": comp_pivot[f"{comp_year}_Rent_PSF"]
            })
            if selected_compare_warehouses:
                ledger_display = ledger_display[ledger_display["CMP ID"].isin(selected_compare_warehouses)]
                
            fmt_comp = {"Total Area": "{:,.0f} Sq. Ft.", f"{base_year} Rev/PSF": "₹{:.2f}/sf", f"{base_year} Rent/PSF": "₹{:.2f}/sf", f"{comp_year} Rev/PSF": "₹{:.2f}/sf", f"{comp_year} Rent/PSF": "₹{:.2f}/sf"}
            st.dataframe(ledger_display.style.format(fmt_comp), use_container_width=True)
        else:
            st.info("No active locations recorded across both filtered timelines.")

# =========================================================================
# TAB 4: INDIVIDUAL WAREHOUSE DRILLDOWN
# =========================================================================
with tab4:
    st.header("🔍 Granular Asset Investigation Desk")
    selected_facility = st.selectbox("Select Target Facility to Inspect", sorted(df_raw["CMP ID"].unique()))
    facility_profile = df_raw[df_raw["CMP ID"] == selected_facility]
    month_cols = [col for col in df_raw.columns if any(year in str(col) for year in ["2023", "2024", "2025", "2026"])]
    
    if not facility_profile.empty and len(month_cols) > 0:
        st.metric("Storage Volume Capacity (MT)", f"{facility_profile['Capacity'].values[0]:,} MT")
        timeline_df = facility_profile.melt(id_vars=["Details"], value_vars=month_cols, var_name="Month", value_name="Amount")
        timeline_df["Month"] = pd.to_datetime(timeline_df["Month"])
        timeline_df = timeline_df.sort_values("Month")
        
        fig_time = px.line(timeline_df, x="Month", y="Amount", color="Details", markers=True, color_discrete_map={"Rent": "#EF553B", "Rev": "#00CC96"})
        st.plotly_chart(fig_time, use_container_width=True)
