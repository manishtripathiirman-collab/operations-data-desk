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
# 1. DATA INGESTION & CLEANING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    try:
        df_raw_dirty = pd.read_excel(file_path, sheet_name="RAW Data")
        df_rent_dirty = pd.read_excel(file_path, sheet_name="Rent Data", skiprows=1)
        
        # Clean RAW Data sheet columns and structural spacing anomalies
        df_raw = df_raw_dirty.copy()
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        
        if "Cluster" in df_raw.columns:
            df_raw["Cluster"] = df_raw["Cluster"].astype(str).str.strip()
        if "Type" in df_raw.columns:
            df_raw["Type"] = df_raw["Type"].astype(str).str.strip()
            
        # Standard target fiscal tracking horizons
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        for fy in target_fys:
            if fy in df_raw.columns:
                df_raw[fy] = pd.to_numeric(df_raw[fy], errors='coerce').fillna(0.0)
            else:
                df_raw[fy] = 0.0
                
        # --- Clean Rent Data Sheet Columns and Text Metrics Safely ---
        df_rent = df_rent_dirty.copy()
        df_rent.columns = [str(col).strip() for col in df_rent.columns]
        
        # Robust Dynamic Matcher Loops with position fallbacks to prevent IndexError
        wh_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["CODE", "CMP", "WAREHOUSE", "WH", "ID"])]
        wh_code_col = wh_matches[0] if wh_matches else df_rent.columns[0]
        
        rev_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["REV", "INCOME", "BILL", "EARN", "TURN"])]
        rev_col = rev_matches[0] if rev_matches else (df_rent.columns[1] if len(df_rent.columns) > 1 else df_rent.columns[0])
        
        rent_matches = [c for c in df_rent.columns if any(k in c.upper() for k in ["RENT", "OUTFLOW", "EXPENSE", "COST", "FIXED"])]
        rent_col = rent_matches[0] if rent_matches else (df_rent.columns[2] if len(df_rent.columns) > 2 else df_rent.columns[0])
        
        # Process clean calculations
        df_rent["Warehouse Code Normalized"] = df_rent[wh_code_col].astype(str).str.strip().str.upper()
        df_rent["Monthly Revenue"] = pd.to_numeric(df_rent[rev_col], errors='coerce').fillna(0.0)
        df_rent["Monthly Rent"] = pd.to_numeric(df_rent[rent_col], errors='coerce').fillna(0.0)
        
        return df_raw, df_rent, target_fys

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse Excel sheets. Details: {str(e)}")
        st.stop()

# Repository source layout checkpoint
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_raw, df_rent, available_fys = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (BULLETPROOF MASKING STRATEGY)
# --------------------------------------------------------------------
def build_runtime_fy_dataset(fy_target):
    # Dynamically extract tracking variables mapped exactly to horizontal rows
    rev_df = df_raw[df_raw["Type"] == "Rev"]
    rent_df = df_raw[df_raw["Type"] == "Rent"]
    cap_df = df_raw[df_raw["Type"] == "Cap"]
    
    # Extract unique facilities to map coordinates safely
    unique_facilities = df_raw.drop_duplicates(subset=["CMP ID"]).copy()
    
    records = []
    for _, f in unique_facilities.iterrows():
        cid = f["CMP ID"]
        cluster = f["Cluster"]
        
        # Filter down to the specific warehouse code to prevent lookup duplication crashes
        rev_match = rev_df[rev_df["CMP ID"] == cid][fy_target]
        rent_match = rent_df[rent_df["CMP ID"] == cid][fy_target]
        cap_match = cap_df[cap_df["CMP ID"] == cid][fy_target]
        
        # Sum up values if duplicates exist, otherwise get the safe baseline float value
        rev_val = float(rev_match.sum()) if not rev_match.empty else 0.0
        rent_val = float(rent_match.sum()) if not rent_match.empty else 0.0
        cap_val = float(cap_match.sum()) if not cap_match.empty else 0.0
        
        area_val = cap_val * MT_TO_SQFT_CONVERSION
        net_surplus = rev_val - rent_val
        
        # Protective division boundaries for full dehires (Capacity = 0)
        rev_psf = (rev_val / area_val) if area_val > 0 else 0.0
        rent_psf = (rent_val / area_val) if area_val > 0 else 0.0
        
        records.append({
            "CMP ID": cid,
            "Cluster": cluster,
            "Rev": rev_val,
            "Rent": rent_val,
            "Cap": cap_val,
            "Area_SqFt": area_val,
            "Net_Surplus": net_surplus,
            "Rev_PSF": rev_psf,
            "Rent_PSF": rent_psf
        })
        
    return pd.DataFrame(records)

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.sidebar.selectbox(
    "Target Fiscal Year Focus",
    options=available_fys,
    index=min(1, len(available_fys)-1) if available_fys else 0
)

# Extract changing capacity profiles matching current chosen timeline footprint bounds
current_caps = df_raw[df_raw["Type"] == "Cap"][selected_fy]
min_cap_val = int(current_caps.min()) if not current_caps.empty else 0
max_cap_val = int(current_caps.max()) if not current_caps.empty else 100000

capacity_range = st.sidebar.slider(
    f"Active Capacity Boundary ({selected_fy})",
    min_value=min_cap_val,
    max_value=max_cap_val,
    value=(min_cap_val, max_cap_val),
    help="CRITICAL FILTER RULE: Slider values only limit Tab 1 views. Rest of history tools remain unfiltered to preserve lifecycle context."
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
    
    # Extract dynamic runtime dataset matching your raw design metrics
    active_fy_df = build_runtime_fy_dataset(selected_fy)
    
    # Apply filter rule strictly to Tab 1 assets
    filtered_tab1 = active_fy_df[
        (active_fy_df["Cap"] >= capacity_range[0]) & 
        (active_fy_df["Cap"] <= capacity_range[1])
    ]
    
    if filtered_tab1.empty:
        st.warning("⚠️ No warehouse allocations match the chosen Capacity range slider parameters.")
    else:
        # High-Impact Performance Metrics Calculation
        total_rev = filtered_tab1["Rev"].sum()
        total_rent = filtered_tab1["Rent"].sum()
        net_contribution = total_rev - total_rent
        rent_efficiency = (total_rent / total_rev * 100) if total_rev > 0 else 0.0
        
        # Spatial Metrics Conversion Block
        unique_warehouses = filtered_tab1.drop_duplicates(subset=["CMP ID"])
        total_capacity_mt = unique_warehouses["Cap"].sum()
        total_area_sqft = total_capacity_mt * MT_TO_SQFT_CONVERSION
        
        macro_rev_psf = (total_rev / total_area_sqft) if total_area_sqft > 0 else 0.0
        macro_rent_psf = (total_rent / total_area_sqft) if total_area_sqft > 0 else 0.0
        
        # UI Metrics Display Row 1
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
        row1_col1.metric("Total Revenue", f"₹{total_rev:,.2f}")
        row1_col2.metric("Total Fixed Rent", f"₹{total_rent:,.2f}")
        row1_col3.metric("Net Contribution Surplus", f"₹{net_contribution:,.2f}")
        row1_col4.metric("Rent-to-Revenue Efficiency", f"{rent_efficiency:.2f}%")
        
        st.markdown("---")
        
        # UI Metrics Display Row 2
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row2_col1.metric("Total Area Leased", f"{total_area_sqft:,.0f} Sq. Ft.", f"{total_capacity_mt:,.0f} MT")
        row2_col2.metric("Macro Revenue / Sq. Ft.", f"₹{macro_rev_psf:,.2f}/sf")
        row2_col3.metric("Macro Rent / Sq. Ft.", f"₹{macro_rent_psf:,.2f}/sf")
        
        st.markdown("---")
        
        # Parallel Visualizations Layout
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.markdown("#### Top 10 Revenue Generating Clusters")
            cluster_data = filtered_tab1.groupby("Cluster")["Rev"].sum().reset_index()
            cluster_data = cluster_data.sort_values(by="Rev", ascending=True).tail(10)
            fig_cluster = px.bar(
                cluster_data, x="Rev", y="Cluster", orientation='h', 
                template="plotly_white", color="Rev", color_continuous_scale="Agsunset",
                labels={"Rev": "Total Revenue (₹)", "Cluster": "Cluster"}
            )
            fig_cluster.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_cluster, use_container_width=True)
            
        with viz_col2:
            st.markdown("#### Financial Allocation Profiler (Rent vs Revenue)")
            fig_scatter = px.scatter(
                filtered_tab1, x="Rev", y="Rent", hover_name="CMP ID", 
                labels={"Rev": "Revenue (₹)", "Rent": "Rent (₹)"}, 
                trendline="ols", template="plotly_white"
            )
            fig_scatter.update_traces(marker=dict(size=12, color="#1F77B4", opacity=0.75))
            fig_scatter.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_scatter, use_container_width=True)

# ====================================================================
# TAB 2: YOY SQ. FT. RENT ANALYZER
# ====================================================================
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Pricing Velocity Tracker")
    st.caption("🔒 Seasoned Asset Filter Active: Displays facilities tracking data for 2 or more years.")
    
    # Process histories accurately via context building block
    y23_base = build_runtime_fy_dataset("FY 23-24")
    y24_base = build_runtime_fy_dataset("FY 24-25")
    y25_base = build_runtime_fy_dataset("FY 25-26")
    
    # Map out how many years each warehouse shows active leased tracking > 0
    active_tracker = pd.DataFrame({
        "CMP ID": y24_base["CMP ID"],
        "Y23_Active": y23_base["Cap"] > 0,
        "Y24_Active": y24_base["Cap"] > 0,
        "Y25_Active": y25_base["Cap"] > 0
    })
    active_tracker["Total_Active_Years"] = active_tracker[["Y23_Active", "Y24_Active", "Y25_Active"]].sum(axis=1)
    seasoned_list = active_tracker[active_tracker["Total_Active_Years"] >= 2]["CMP ID"].tolist()
    
    # Build a clean melted tracking matrix for chart configurations
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
        # Interactive Multi-Select Filter
        all_seasoned_codes = sorted(df_yoy_final["CMP ID"].unique())
        target_assets = st.multiselect(
            "Isolate Specific Qualified Assets (Leave empty to view all standard portfolio assets):", 
            options=all_seasoned_codes, key="tab2_multiselect"
        )
        
        filtered_yoy = df_yoy_final.copy()
        if target_assets:
            filtered_yoy = filtered_yoy[filtered_yoy["CMP ID"].isin(target_assets)]
            
        # Year over Year Grouped Clustered Bar Chart
        fig_yoy = px.bar(
            filtered_yoy, x="CMP ID", y="Rent_PSF", color="Fiscal Year",
            barmode="group", color_discrete_map=FY_COLORS, template="plotly_white",
            labels={"Rent_PSF": "Rent Rate (₹ / Sq. Ft.)", "CMP ID": "Warehouse Code ID"}
        )
        fig_yoy.update_layout(xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig_yoy, use_container_width=True)
        
        # Grid Ledger Matrix Display
        st.markdown("#### Dynamic Area & Unit Pricing Ledger")
        ledger_pivot = filtered_yoy.pivot(index=["CMP ID", "Cluster"], columns="Fiscal Year", values=["Area_SqFt", "Rent_PSF"])
        
        fmt_config = {}
        for yr in ["FY 23-24", "FY 24-25", "FY 25-26"]:
            if ("Area_SqFt", yr) in ledger_pivot.columns:
                fmt_config[("Area_SqFt", yr)] = "{:,.0f} Sq. Ft."
            if ("Rent_PSF", yr) in ledger_pivot.columns:
                fmt_config[("Rent_PSF", yr)] = "₹{:.2f}/sf"
            
        st.dataframe(ledger_pivot.fillna(0.0).style.format(fmt_config), use_container_width=True)

# ====================================================================
# TAB 3: COMPARE TWO YEARS
# ====================================================================
with tabs[2]:
    st.subheader("Arbitrary Milestone Timeline Cross-Examiner Engine")
    
    # Dual Sidebar Selection Toggles
    col_x, col_y = st.columns(2)
    with col_x: year_alpha = st.selectbox("Select Timeline Baseline (Year 1)", options=available_fys, index=0)
    with col_y: year_beta = st.selectbox("Select Timeline Target (Year 2)", options=available_fys, index=min(2, len(available_fys)-1))
    
    if year_alpha == year_beta:
        st.warning("⚠️ Baseline and Target profiles are uniform. Select different historical years to generate variance spreads.")
        
    df_alpha = build_runtime_fy_dataset(year_alpha)
    df_beta = build_runtime_fy_dataset(year_beta)
    
    merged_comp = pd.merge(df_alpha, df_beta, on=["CMP ID", "Cluster"], suffixes=("_Base", "_Comp"))
    
    # Visual Concentric Overlay Engine Chart
    fig_compare = go.Figure()
    # Baseline Parameters (Year 1)
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Base"], name=f"Rev PSF ({year_alpha})", marker_color="#A6C8E0", offsetgroup=0))
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Base"], name=f"Rent PSF ({year_alpha})", marker_color="#1F77B4", width=0.2, offsetgroup=0))
    # Target Parameters (Year 2)
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Comp"], name=f"Rev PSF ({year_beta})", marker_color="#FFC19E", offsetgroup=1))
    fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Comp"], name=f"Rent PSF ({year_beta})", marker_color="#FF7F0E", width=0.2, offsetgroup=1))
    
    fig_compare.update_layout(template="plotly_white", barmode="group", yaxis_title="Unit Financial Metric Scale (₹ / Sq. Ft.)", xaxis_tickangle=-45, height=480)
    st.plotly_chart(fig_compare, use_container_width=True)
    
    # Ledger Grid Table Matrix
    st.markdown("#### Performance Matrix Dataset Comparison")
    compare_matrix = merged_comp[["CMP ID", "Cluster", "Rev_PSF_Base", "Rent_PSF_Base", "Rev_PSF_Comp", "Rent_PSF_Comp"]].copy()
    st.dataframe(
        compare_matrix.style.format({
            "Rev_PSF_Base": "₹{:.2f}",
            "Rent_PSF_Base": "₹{:.2f}",
            "Rev_PSF_Comp": "₹{:.2f}",
            "Rent_PSF_Comp": "₹{:.2f}"
        }),
        use_container_width=True
    )

# ====================================================================
# TAB 4: INDIVIDUAL WAREHOUSE DRILLDOWN
# ====================================================================
with tabs[3]:
    st.subheader("Granular Individual Property Footprint Lifecycle Review")
    
    # Dropdown Facility Selector
    alphabetical_codes = sorted(df_raw["CMP ID"].unique())
    target_wh = st.selectbox("Select Specific Target Facility for Deep-Dive Analysis:", options=alphabetical_codes)
    
    # Monthly Timeline Graph
    monthly_slice = df_rent[df_rent["Warehouse Code Normalized"] == target_wh]
    
    if monthly_slice.empty:
        st.info("📊 No granular sub-month logging rows detected for this asset ID.")
    else:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=monthly_slice["Month"], y=monthly_slice["Monthly Revenue"], mode='lines+markers', name='Monthly Revenue Channel', line=dict(color='#2CA02C', width=3)))
        fig_trend.add_trace(go.Scatter(x=monthly_slice["Month"], y=monthly_slice["Monthly Rent"], mode='lines+markers', name='Monthly Rent Outflow', line=dict(color='#D62728', width=2, dash='dot')))
        fig_trend.update_layout(template="plotly_white", title=f"Continuous Operational Sequence Tracker for Asset: {target_wh}", yaxis_title="Financial Value Scales (₹)", height=360)
        st.plotly_chart(fig_trend, use_container_width=True)
        
    st.markdown("#### Annual Macro Allocation Accounting Spread")
    
    # Consolidated Summary Matrix Data Assembly
    history_rows = []
    for yr in available_fys:
        fy_df = build_runtime_fy_dataset(yr)
        match_row = fy_df[fy_df["CMP ID"] == target_wh]
        if not match_row.empty:
            r = match_row.iloc[0]
            history_rows.append({
                "Year": yr,
                "Rev": r["Rev"],
                "Rent": r["Rent"],
                "Net Margin surplus": r["Net_Surplus"]
            })
            
    if history_rows:
        df_history_grid = pd.DataFrame(history_rows).set_index("Year").T
        
        # CRITICAL STYLING RULE: Target only the numeric year columns explicitly when configuring currency formatting string templates
        fmt_target = {col: "₹{:,.0f}" for col in df_history_grid.columns}
        st.dataframe(df_history_grid.style.format(fmt_target), use_container_width=True)
