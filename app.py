import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------------------------
# 0. APP CONFIGURATION & CONSTANTS
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Warehouse Performance & Dehire Analyzer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

MT_TO_SQFT_CONVERSION = 6.0
FY_COLORS = {
    "FY 23-24": "#2CA02C",  # Green
    "FY 24-25": "#FFD700",  # Yellow
    "FY 25-26": "#D62728"   # Magenta
}

# --------------------------------------------------------------------
# 1. DATA INGESTION & ROBUST CLEANING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    # Safe multi-sheet reading from uploaded source file
    try:
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # Clean RAW Data sheet columns and spaces
        df_raw = df_raw_dirty.copy()
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Type" in df_raw.columns:
            df_raw["Type"] = df_raw["Type"].astype(str).str.strip()
            
        # Target financial and capacity columns natively
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        for fy in target_fys:
            if fy in df_raw.columns:
                df_raw[fy] = pd.to_numeric(df_raw[fy], errors='coerce').fillna(0.0)
            else:
                df_raw[fy] = 0.0
                
        # Clean Rent Data sheet columns and titles
        df_rent = df_rent_dirty.copy()
        df_rent.columns = [str(col).strip() for col in df_rent.columns]
        
        wh_code_col = [c for c in df_rent.columns if "CODE" in c.upper() or "CMP" in c.upper() or "WAREHOUSE" in c.upper()][0]
        rev_col = [c for c in df_rent.columns if "REV" in c.upper()][0]
        rent_col = [c for c in df_rent.columns if "RENT" in c.upper()][0]
        
        df_rent["Warehouse Code Normalized"] = df_rent[wh_code_col].astype(str).str.strip().str.upper()
        df_rent["Monthly Revenue"] = pd.to_numeric(df_rent[rev_col], errors='coerce').fillna(0.0)
        df_rent["Monthly Rent"] = pd.to_numeric(df_rent[rent_col], errors='coerce').fillna(0.0)
        
        return df_raw, df_rent, target_fys

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse Excel sheets. Details: {str(e)}")
        st.stop()

# Auto-loading setup from your GitHub repository folder link structure
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_raw, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. DATA PIVOTING & TRANSFORMATION ENGINE (DEHIRE PROOFED)
# --------------------------------------------------------------------
# Restructure raw rows so every warehouse has mapped rows for Rev, Rent, and Cap simultaneously
pivoted_portfolio = df_raw.pivot(index=["CMP ID", "Cluster"], columns="Type").reset_index()

def build_runtime_fy_dataset(fy_target):
    # Safe checks if type markers are missing in source sheets
    rev_source = pivoted_portfolio[(fy_target, "Rev")] if (fy_target, "Rev") in pivoted_portfolio.columns else pd.Series(0.0, index=pivoted_portfolio.index)
    rent_source = pivoted_portfolio[(fy_target, "Rent")] if (fy_target, "Rent") in pivoted_portfolio.columns else pd.Series(0.0, index=pivoted_portfolio.index)
    cap_source = pivoted_portfolio[(fy_target, "Cap")] if (fy_target, "Cap") in pivoted_portfolio.columns else pd.Series(0.0, index=pivoted_portfolio.index)

    df_step = pd.DataFrame({
        "CMP ID": pivoted_portfolio["CMP ID"],
        "Cluster": pivoted_portfolio["Cluster"],
        "Rev": rev_source,
        "Rent": rent_source,
        "Cap": cap_source
    })
    
    # Calculate space conversion and net margin streams
    df_step["Area_SqFt"] = df_step["Cap"] * MT_TO_SQFT_CONVERSION
    df_step["Net_Surplus"] = df_step["Rev"] - df_step["Rent"]
    
    # Defensive handling for full dehired spaces (Capacity = 0) to avoid DivisionByZero crashes
    df_step["Rev_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rev"] / df_step["Area_SqFt"], 0.0)
    df_step["Rent_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rent"] / df_step["Area_SqFt"], 0.0)
    return df_step

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.sidebar.selectbox(
    "Target Fiscal Year Focus",
    options=available_fys,
    index=min(1, len(available_fys)-1) # Safely defaults to FY 24-25 if available
)

# Extract changing capacity metrics for slider boundaries relative to chosen year footprint
current_caps = df_raw[df_raw["Type"] == "Cap"][selected_fy]
min_cap_val = int(current_caps.min()) if not current_caps.empty else 0
max_cap_val = int(current_caps.max()) if not current_caps.empty else 100000

capacity_range = st.sidebar.slider(
    f"Active Capacity Boundary ({selected_fy})",
    min_value=min_cap_val,
    max_value=max_cap_val,
    value=(min_cap_val, max_cap_val),
    help="CRITICAL FILTER RULE: Slider values only limit Tab 1 views. Rest of history tools remain unfiltered to preserve context."
)

# --------------------------------------------------------------------
# 4. STRUCTURAL ARCHITECTURE (4 HIGH-PERFORMANCE TABS)
# --------------------------------------------------------------------
tabs = st.tabs([
    "📈 Portfolio Performance Summary",
    "🔄 YoY Sq. Ft. Rent Analyzer",
    "📊 Compare Two Years",
    "🔍 Individual Warehouse Drilldown"
])

# ====================================================================
# TAB 1: PORTFOLIO PERFORMANCE SUMMARY
# ====================================================================
with tabs[0]:
    st.subheader(f"Portfolio Financial & Footprint Summary Matrix — {selected_fy}")
    
    # Extract dynamic runtime dataset
    active_fy_df = build_runtime_fy_dataset(selected_fy)
    
    # Apply filter rule strictly to Tab 1 assets
    filtered_tab1 = active_fy_df[
        (active_fy_df["Cap"] >= capacity_range[0]) & 
        (active_fy_df["Cap"] <= capacity_range[1])
    ]
    
    if filtered_tab1.empty:
        st.warning("⚠️ No warehouse allocations match the chosen Capacity range slider parameters.")
    else:
        # High-Impact Metrics Execution
        total_rev = filtered_tab1["Rev"].sum()
        total_rent = filtered_tab1["Rent"].sum()
        total_surplus = filtered_tab1["Net_Surplus"].sum()
        rent_efficiency = (total_rent / total_rev * 100) if total_rev > 0 else 0.0
        
        total_area_sqft = filtered_tab1["Area_SqFt"].sum()
        macro_rev_psf = (total_rev / total_area_sqft) if total_area_sqft > 0 else 0.0
        macro_rent_psf = (total_rent / total_area_sqft) if total_area_sqft > 0 else 0.0
        
        # Row 1 Display
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Gained Revenue", f"₹{total_rev:,.2f}")
        m2.metric("Total Rent Outflow", f"₹{total_rent:,.2f}")
        m3.metric("Net Surplus Contribution", f"₹{total_surplus:,.2f}")
        m4.metric("Rent-to-Revenue Efficiency", f"{rent_efficiency:.2f}%")
        
        st.markdown("---")
        
        # Row 2 Display
        mr1, mr2, mr3 = st.columns(3)
        mr1.metric("Active Footprint Leased", f"{total_area_sqft:,.0f} Sq. Ft.", f"{filtered_tab1['Cap'].sum():,.0f} MT active")
        mr2.metric("Macro Revenue / Sq. Ft.", f"₹{macro_rev_psf:.2f}/sf")
        mr3.metric("Macro Rent / Sq. Ft.", f"₹{macro_rent_psf:.2f}/sf")
        
        st.markdown("---")
        
        # Parallel Visualizations Layout
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.markdown("#### Top 10 Revenue Clusters")
            cluster_data = filtered_tab1.groupby("Cluster")["Rev"].sum().reset_index()
            cluster_data = cluster_data.sort_values(by="Rev", ascending=True).tail(10)
            fig_cluster = px.bar(cluster_data, x="Rev", y="Cluster", orientation='h', template="plotly_white", color="Rev", color_continuous_scale="Agsunset")
            fig_cluster.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_cluster, use_container_width=True)
            
        with viz_col2:
            st.markdown("#### Operational Capacity Allocation Profiler")
            fig_scatter = px.scatter(filtered_tab1, x="Area_SqFt", y="Rent", hover_name="CMP ID", labels={"Area_SqFt": "Active Footprint (Sq. Ft.)", "Rent": "Rent Commitment (₹)"}, trendline="ols", template="plotly_white")
            fig_scatter.update_traces(marker=dict(size=12, color="#D62728", opacity=0.75))
            fig_scatter.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_scatter, use_container_width=True)

# ====================================================================
# TAB 2: YOY SQ. FT. RENT ANALYZER (DEHIRE PROOFED)
# ====================================================================
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Velocity Analyzer")
    st.caption("🔒 Seasoned Asset Filter Active: Displays facilities tracking data for 2 or more years. Rent PSF remains stabilized during space dehiring.")
    
    # Track seasoned assets across space lifecycle changes
    y23_base = build_runtime_fy_dataset("FY 23-24")
    y24_base = build_runtime_fy_dataset("FY 24-25")
    y25_base = build_runtime_fy_dataset("FY 25-26")
    
    # Count how many years each warehouse has an active capacity profile > 0
    active_tracker = pd.DataFrame({
        "CMP ID": pivoted_portfolio["CMP ID"],
        "Y23_Active": y23_base["Cap"] > 0,
        "Y24_Active": y24_base["Cap"] > 0,
        "Y25_Active": y25_base["Cap"] > 0
    })
    active_tracker["Total_Active_Years"] = active_tracker[["Y23_Active", "Y24_Active", "Y25_Active"]].sum(axis=1)
    seasoned_list = active_tracker[active_tracker["Total_Active_Years"] >= 2]["CMP ID"].tolist()
    
    # Build complete timeline data frame for seasoned components
    yoy_records = []
    for yr_lbl, yr_df in [("FY 23-24", y23_base), ("FY 24-25", y24_base), ("FY 25-26", y25_base)]:
        for _, row in yr_df.iterrows():
            if row["CMP ID"] in seasoned_list and row["Cap"] > 0:
                yoy_records.append({
                    "CMP ID": row["CMP ID"],
                    "Cluster": row["Cluster"],
                    "Fiscal Year": yr_lbl,
                    "Rent_PSF": row["Rent_PSF"],
                    "Area_SqFt": row["Area_SqFt"]
                })
    df_yoy_final = pd.DataFrame(yoy_records)
    
    if df_yoy_final.empty:
        st.info("No seasoned properties found across history files.")
    else:
        # Multiselect Filter Panel
        all_seasoned_codes = sorted(df_yoy_final["CMP ID"].unique())
        target_assets = st.multiselect("Isolate Properties (Leave blank to display full portfolio):", options=all_seasoned_codes)
        
        filtered_yoy = df_yoy_final.copy()
        if target_assets:
            filtered_yoy = filtered_yoy[filtered_yoy["CMP ID"].isin(target_assets)]
            
        # Clustered Bar Graph
        fig_yoy = px.bar(
            filtered_yoy, x="CMP ID", y="Rent_PSF", color="Fiscal Year",
            barmode="group", color_discrete_map=FY_COLORS, template="plotly_white",
            labels={"Rent_PSF": "Rent Rate (₹ / Sq. Ft.)", "CMP ID": "Warehouse Code ID"}
        )
        fig_yoy.update_layout(xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig_yoy, use_container_width=True)
        
        # Grid Ledger Matrix Layout
        st.markdown("#### Dynamic Area & Unit Pricing Ledger")
        ledger_pivot = filtered_yoy.pivot(index=["CMP ID", "Cluster"], columns="Fiscal Year", values=["Area_SqFt", "Rent_PSF"])
        
        # Construct clean multi-index format map to secure system against formatting exceptions
        fmt_config = {}
        for yr in ["FY 23-24", "FY 24-25", "FY 25-26"]:
            fmt_config[("Area_SqFt", yr)] = "{:,.0f} sf"
            fmt_config[("Rent_PSF", yr)] = "₹{:.2f}/sf"
            
        st.dataframe(ledger_pivot.fillna(0.0).style.format(fmt_config), use_container_width=True)

# ====================================================================
# TAB 3: COMPARE TWO YEARS
# ====================================================================
with tabs[2]:
    st.subheader("Cross-Timeline Performance & Margin Spread Audit")
    
    # Dual Selection Columns
    col_x, col_y = st.columns(2)
    with col_x: year_alpha = st.selectbox("Select Timeline Baseline", options=available_fys, index=0)
    with col_y: year_beta = st.selectbox("Select Timeline Target", options=available_fys, index=min(2, len(available_fys)-1))
    
    if year_alpha == year_beta:
        st.warning("⚠️ Baseline and Target profiles are uniform. Select different historical years to generate variance spreads.")
        
    df_alpha = build_runtime_fy_dataset(year_alpha)
    df_beta = build_runtime_fy_dataset(year_beta)
    
    merged_comp = pd.merge(df_alpha, df_beta, on=["CMP ID", "Cluster"], suffixes=("_Base", "_Comp"))
    
    # Visual Concentric Bar Graph Construction
    fig_compare = go.Figure()
    # Baseline Year Parameters
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Base"], name=f"Rev PSF ({year_alpha})", marker_color="#A6C8E0", offsetgroup=0))
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Base"], name=f"Rent PSF ({year_alpha})", marker_color="#1F77B4", width=0.2, offsetgroup=0))
    # Target Year Parameters
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Comp"], name=f"Rev PSF ({year_beta})", marker_color="#FFC19E", offsetgroup=1))
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Comp"], name=f"Rent PSF ({year_beta})", marker_color="#FF7F0E", width=0.2, offsetgroup=1))
    
    fig_compare.update_layout(template="plotly_white", barmode="group", yaxis_title="Unit Financial Metric Scale (₹ / Sq. Ft.)", xaxis_tickangle=-45, height=480)
    st.plotly_chart(fig_compare, use_container_width=True)
    
    st.markdown("#### Performance Grid Breakdown Matrix")
    compare_matrix = merged_comp[["CMP ID", "Cluster", "Cap_Base", "Rent_PSF_Base", "Cap_Comp", "Rent_PSF_Comp"]].copy()
    st.dataframe(
        compare_matrix.style.format({
            "Cap_Base": "{:,.0f} MT", "Rent_PSF_Base": "₹{:.2f}",
            "Cap_Comp": "{:,.0f} MT", "Rent_PSF_Comp": "₹{:.2f}"
        }),
        use_container_width=True
    )

# ====================================================================
# TAB 4: INDIVIDUAL WAREHOUSE DRILLDOWN
# ====================================================================
with tabs[3]:
    st.subheader("Granular Individual Property Footprint Lifecycle Review")
    
    alphabetical_codes = sorted(df_raw["CMP ID"].unique())
    target_wh = st.selectbox("Isolate Facility Profile Lookup Vector:", options=alphabetical_codes)
    
    # Process monthly chronological charts if available
    monthly_slice = df_rent[df_rent["Warehouse Code Normalized"] == target_wh]
    
    if monthly_slice.empty:
        st.info("📊 No granular sub-month logging rows detected for this asset ID.")
    else:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=monthly_slice["Month"], y=monthly_slice["Monthly Revenue"], mode='lines+markers', name='Monthly Revenue Channel', line=dict(color='#2CA02C', width=3)))
        fig_trend.add_trace(go.Scatter(x=monthly_slice["Month"], y=monthly_slice["Monthly Rent"], mode='lines+markers', name='Monthly Rent Outflow', line=dict(color='#D62728', width=2, dash='dot')))
        fig_trend.update_layout(template="plotly_white", title=f"Continuous Operational Sequence Tracker for Asset: {target_wh}", yaxis_title="Financial Value Scales (₹)", height=360)
        st.plotly_chart(fig_trend, use_container_width=True)
        
    st.markdown("#### Historical Footprint Tracking Matrix")
    
    # Re-extract and isolate timeline records
    history_rows = []
    for yr in available_fys:
        fy_df = build_runtime_fy_dataset(yr)
        match_row = fy_df[fy_df["CMP ID"] == target_wh]
        if not match_row.empty:
            r = match_row.iloc[0]
            history_rows.append({
                "Timeline Context": yr,
                "Revenue Runrate": r["Rev"],
                "Rent Charge": r["Rent"],
                "Capacity Footprint": f"{r['Cap']:,.0f} MT ({r['Area_SqFt']:,.0f} Sq. Ft.)",
                "Net Surplus Margin": r["Net_Surplus"]
            })
            
    if history_rows:
        df_history_grid = pd.DataFrame(history_rows).set_index("Timeline Context")
        
        # Structural financial matrix layout
        st.dataframe(
            df_history_grid.T.style.format({
                "FY 23-24": "₹{:,.2f}" if isinstance(df_history_grid.loc["FY 23-24", "Revenue Runrate"], (int, float)) else "{}",
                "FY 24-25": "₹{:,.2f}" if isinstance(df_history_grid.loc["FY 24-25", "Revenue Runrate"], (int, float)) else "{}",
                "FY 25-26": "₹{:,.2f}" if isinstance(df_history_grid.loc["FY 25-26", "Revenue Runrate"], (int, float)) else "{"
            }, na_rep="-"),
            use_container_width=True
        )
