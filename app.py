import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

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

# Helper to clean and group cluster names automatically from CMP ID strings
def clean_cluster_name(cmp_id):
    match = re.match(r'^([a-zA-Z\s\-\(\)]+)', str(cmp_id))
    if match:
        return match.group(1).strip().upper()
    return "STANDARD-GROUP"

# --------------------------------------------------------------------
# 1. HORIZONTAL MATRIX DATA INGESTION & PROCESSING LAYER
# --------------------------------------------------------------------
@st.cache_data
def load_and_clean_warehouse_data(file_path):
    try:
        # Load rows directly from worksheet matrix
        df_raw = pd.read_excel(file_path, sheet_name="RAW Data")
        df_raw.columns = [str(col).strip() for col in df_raw.columns]
        df_raw["CMP ID"] = df_raw["CMP ID"].astype(str).str.strip().str.upper()
        df_raw["Cluster"] = df_raw["CMP ID"].apply(clean_cluster_name)
        df_raw["Type_Clean"] = df_raw["Details"].astype(str).str.strip().str.lower()
        
        # Isolate chronological monthly tracking columns from metadata headers
        date_cols = []
        for col in df_raw.columns:
            if col.startswith("2023") or col.startswith("2024") or col.startswith("2025") or col.startswith("2026"):
                date_cols.append(col)
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
                
        # Group single month columns into true Indian Fiscal Years (April to March)
        fy_groups = {
            "FY 23-24": [c for c in date_cols if (c >= "2023-04-01" and c <= "2024-03-01")],
            "FY 24-25": [c for c in date_cols if (c >= "2024-04-01" and c <= "2025-03-01")],
            "FY 25-26": [c for c in date_cols if (c >= "2025-04-01" and c <= "2026-03-01")]
        }
        
        unique_warehouses = df_raw["CMP ID"].unique()
        portfolio_records = []
        
        for cid in unique_warehouses:
            wh_rows = df_raw[df_raw["CMP ID"] == cid]
            cluster_val = wh_rows["Cluster"].iloc[0]
            
            # Map clean rows based on exact tokens present in details index
            rev_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rev|revenue|income", na=False)]
            rent_rows = wh_rows[wh_rows["Type_Clean"].str.contains("rent|fixed", na=False)]
            cap_rows = wh_rows[wh_rows["Type_Clean"].str.contains("cap|capacity|space", na=False)]
            
            for fy_name, columns_in_fy in fy_groups.items():
                if not columns_in_fy:
                    continue
                    
                # Financial parameters are aggregated horizontally via sum total
                rev_val = float(rev_rows[columns_in_fy].sum().sum()) if not rev_rows.empty else 0.0
                rent_val = float(rent_rows[columns_in_fy].sum().sum()) if not rent_rows.empty else 0.0
                
                # Capacity parameter maps average across active months to capture dehire timeline steps precisely
                cap_val = float(cap_rows[columns_in_fy].mean().mean()) if not cap_rows.empty else 0.0
                if np.isnan(cap_val):
                    cap_val = 0.0
                    
                portfolio_records.append({
                    "CMP ID": cid,
                    "Cluster": cluster_val,
                    "Fiscal Year": fy_name,
                    "Rev": rev_val,
                    "Rent": rent_val,
                    "Cap": cap_val
                })
                
        df_portfolio = pd.DataFrame(portfolio_records)
        target_fys = ["FY 23-24", "FY 24-25", "FY 25-26"]
        
        return df_portfolio, target_fys, df_raw, date_cols

    except Exception as e:
        st.error(f"🚨 Ingestion Layer Fatal Error: Failed to parse raw matrix columns. Details: {str(e)}")
        st.stop()

# Repository configuration setup
target_excel_filename = "Rent Analysis Data.xlsx"

try:
    df_portfolio, available_fys, df_raw_original, chronological_months = load_and_clean_warehouse_data(target_excel_filename)
except FileNotFoundError:
    st.error(f"📂 Critical File Missing: Please ensure **`{target_excel_filename}`** is uploaded into your GitHub repository folder alongside this app script.")
    st.stop()

# --------------------------------------------------------------------
# 2. RUNTIME CONTEXT EXTRACTOR (DEHIRE STABILIZED STRATEGY)
# --------------------------------------------------------------------
def build_runtime_fy_dataset(fy_target):
    df_step = df_portfolio[df_portfolio["Fiscal Year"] == fy_target].copy()
    
    if df_step.empty:
        return pd.DataFrame(columns=["CMP ID", "Cluster", "Rev", "Rent", "Cap", "Area_SqFt", "Net_Surplus", "Rev_PSF", "Rent_PSF"])
        
    df_step["Area_SqFt"] = df_step["Cap"] * MT_TO_SQFT_CONVERSION
    df_step["Net_Surplus"] = df_step["Rev"] - df_step["Rent"]
    
    df_step["Rev_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rev"] / df_step["Area_SqFt"], 0.0)
    df_step["Rent_PSF"] = np.where(df_step["Area_SqFt"] > 0, df_step["Rent"] / df_step["Area_SqFt"], 0.0)
    return df_step

# Highlight styling routines to spotlight best performance margins and worst rent outflows
def spotlight_best_performers(s):
    is_max = s == s.max()
    return ['background-color: #D4EDDA; color: #155724; font-weight: bold' if v else '' for v in is_max]

def spotlight_worst_performers(s):
    is_max = s == s.max()
    return ['background-color: #F8D7DA; color: #721C24; font-weight: bold' if v else '' for v in is_max]

# --------------------------------------------------------------------
# 3. GLOBAL CONTROLS & SIDEBAR ENVIRONMENT
# --------------------------------------------------------------------
st.sidebar.title("⚙️ Global Audit Controls")
st.sidebar.markdown("---")

selected_fy = st.sidebar.selectbox(
    "Target Fiscal Year Focus",
    options=available_fys,
    index=available_fys.index("FY 24-25") if "FY 24-25" in available_fys else 0
)

current_caps = df_portfolio[df_portfolio["Fiscal Year"] == selected_fy]["Cap"] if not df_portfolio.empty else pd.Series([0])
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
    
    active_fy_df = build_runtime_fy_dataset(selected_fy)
    
    filtered_tab1 = active_fy_df[
        (active_fy_df["Cap"] >= capacity_range[0]) & 
        (active_fy_df["Cap"] <= capacity_range[1])
    ]
    
    if filtered_tab1.empty:
        st.warning("⚠️ No warehouse allocations match the chosen Capacity range slider parameters.")
    else:
        total_rev = filtered_tab1["Rev"].sum()
        total_rent = filtered_tab1["Rent"].sum()
        net_contribution = total_rev - total_rent
        rent_efficiency = (total_rent / total_rev * 100) if total_rev > 0 else 0.0
        
        total_capacity_mt = filtered_tab1["Cap"].sum()
        total_area_sqft = total_capacity_mt * MT_TO_SQFT_CONVERSION
        
        macro_rev_psf = (total_rev / total_area_sqft) if total_area_sqft > 0 else 0.0
        macro_rent_psf = (total_rent / total_area_sqft) if total_area_sqft > 0 else 0.0
        
        # Display Row 1
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
        row1_col1.metric("Total Revenue", f"₹{total_rev:,.2f}")
        row1_col2.metric("Total Fixed Rent", f"₹{total_rent:,.2f}")
        row1_col3.metric("Net Contribution Surplus", f"₹{net_contribution:,.2f}")
        row1_col4.metric("Rent-to-Revenue Efficiency", f"{rent_efficiency:.2f}%")
        
        st.markdown("---")
        
        # Display Row 2 — Revenue integration pinned as clear context secondary marker
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row2_col1.metric("Total Area Leased", f"{total_area_sqft:,.0f} Sq. Ft.", f"₹{total_rev:,.0f} Total Revenue")
        row2_col2.metric("Macro Revenue / Sq. Ft.", f"₹{macro_rev_psf:,.2f}/sf")
        row2_col3.metric("Macro Rent / Sq. Ft.", f"₹{macro_rent_psf:,.2f}/sf")
        
        st.markdown("---")
        
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.markdown("#### Top 10 Revenue Generating Clusters")
            cluster_data = filtered_tab1.groupby("Cluster")["Rev"].sum().reset_index()
            cluster_data = cluster_data.sort_values(by="Rev", ascending=True).tail(10)
            fig_cluster = px.bar(
                cluster_data, x="Rev", y="Cluster", orientation='h', 
                template="plotly_white", color="Rev", color_continuous_scale="Agsunset",
                labels={"Rev": "Total Revenue (₹)", "Cluster": "Cluster Group"}
            )
            fig_cluster.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_cluster, use_container_width=True)
            
        with viz_col2:
            st.markdown("#### Financial Allocation Profiler (Rent vs Revenue)")
            fig_scatter = px.scatter(
                filtered_tab1, x="Rev", y="Rent", hover_name="CMP ID", 
                labels={"Rev": "Revenue Runway (₹)", "Rent": "Fixed Rent commitment (₹)"}, 
                trendline="ols", template="plotly_white"
            )
            fig_scatter.update_traces(marker=dict(size=12, color="#1F77B4", opacity=0.75))
            fig_scatter.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### 🏆 Portfolio Spotlights (Highest Revenue vs Highest Rent Exposure)")
        spot_col1, spot_col2 = st.columns(2)
        
        with spot_col1:
            st.caption("🟢 Top 5 Highest Yielding Facilities (Max Revenue)")
            top_rev_table = filtered_tab1.sort_values(by="Rev", ascending=False).head(5)[["CMP ID", "Cluster", "Rev", "Rent"]]
            st.dataframe(top_rev_table.style.format({"Rev": "₹{:,.2f}", "Rent": "₹{:,.2f}"}), use_container_width=True)
            
        with spot_col2:
            st.caption("🔴 Top 5 Highest Rent Outflows (Max Exposure)")
            top_rent_table = filtered_tab1.sort_values(by="Rent", ascending=False).head(5)[["CMP ID", "Cluster", "Rev", "Rent"]]
            st.dataframe(top_rent_table.style.format({"Rev": "₹{:,.2f}", "Rent": "₹{:,.2f}"}), use_container_width=True)

# ====================================================================
# TAB 2: YOY SQ. FT. RENT ANALYZER
# ====================================================================
with tabs[1]:
    st.subheader("Year-on-Year Unit Rent Pricing Velocity Tracker")
    st.caption("🔒 Seasoned Asset Filter Active: Displays facilities tracking data for 2 or more years.")
    
    y23_base = build_runtime_fy_dataset("FY 23-24")
    y24_base = build_runtime_fy_dataset("FY 24-25")
    y25_base = build_runtime_fy_dataset("FY 25-26")
    
    all_facilities = df_portfolio["CMP ID"].unique() if not df_portfolio.empty else []
    seasoned_list = []
    for cid in all_facilities:
        active_count = 0
        if cid in y23_base["CMP ID"].values and float(y23_base[y23_base["CMP ID"] == cid]["Cap"].iloc[0]) > 0: active_count += 1
        if cid in y24_base["CMP ID"].values and float(y24_base[y24_base["CMP ID"] == cid]["Cap"].iloc[0]) > 0: active_count += 1
        if cid in y25_base["CMP ID"].values and float(y25_base[y25_base["CMP ID"] == cid]["Cap"].iloc[0]) > 0: active_count += 1
        if active_count >= 2:
            seasoned_list.append(cid)
            
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
                
    if not yoy_records:
        st.info("No seasoned properties matching history criteria discovered.")
    else:
        df_yoy_final = pd.DataFrame(yoy_records)
        all_seasoned_codes = sorted(df_yoy_final["CMP ID"].unique())
        target_assets = st.multiselect(
            "Isolate Specific Qualified Assets (Leave empty to view all qualified assets):", 
            options=all_seasoned_codes, key="tab2_multiselect"
        )
        
        filtered_yoy = df_yoy_final.copy()
        if target_assets:
            filtered_yoy = filtered_yoy[filtered_yoy["CMP ID"].isin(target_assets)]
            
        fig_yoy = px.bar(
            filtered_yoy, x="CMP ID", y="Rent_PSF", color="Fiscal Year",
            barmode="group", color_discrete_map=FY_COLORS, template="plotly_white",
            labels={"Rent_PSF": "Rent Rate (₹ / Sq. Ft.)", "CMP ID": "Warehouse Code ID"}
        )
        fig_yoy.update_layout(xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig_yoy, use_container_width=True)
        
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
    
    col_x, col_y = st.columns(2)
    with col_x: year_alpha = st.selectbox("Select Timeline Baseline (Year 1)", options=available_fys, index=0)
    with col_y: year_beta = st.selectbox("Select Timeline Target (Year 2)", options=available_fys, index=min(2, len(available_fys)-1))
    
    if year_alpha == year_beta:
        st.warning("⚠️ Baseline and Target profiles are uniform. Select different historical years to generate variance spreads.")
        
    df_alpha = build_runtime_fy_dataset(year_alpha)
    df_beta = build_runtime_fy_dataset(year_beta)
    
    if df_alpha.empty or df_beta.empty:
        st.info("Missing comparative historical vectors within database.")
    else:
        merged_comp = pd.merge(df_alpha, df_beta, on=["CMP ID", "Cluster"], suffixes=("_Base", "_Comp"))
        
        # Interactive Warehouse Multi-Select Filter Panel
        all_comp_codes = sorted(merged_comp["CMP ID"].unique().tolist())
        selected_comp_warehouses = st.multiselect(
            "Isolate Specific Facilities for Side-by-Side Cross-Analysis (Leave empty to view all assets):", 
            options=all_comp_codes, key="tab3_multiselect"
        )
        
        if selected_comp_warehouses:
            merged_comp = merged_comp[merged_comp["CMP ID"].isin(selected_comp_warehouses)]
            
        # Grouped Dual Nested Bar Chart Visual Engine
        fig_compare = go.Figure()
        
        # Baseline Year 1 Parameters (Wide light bars backdrop)
        fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Base"], name=f"Rev PSF ({year_alpha})", marker_color="#A6C8E0", offsetgroup=0))
        fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Base"], name=f"Rent PSF ({year_alpha})", marker_color="#1F77B4", width=0.2, offsetgroup=0))
        
        # Target Year 2 Parameters (Narrow dark bars foreground stacked via group offsets)
        fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rev_PSF_Comp"], name=f"Rev PSF ({year_beta})", marker_color="#FFC19E", offsetgroup=1))
        fig_compare.add_trace(go.Bar(x=merged_comp["CMP ID"], y=merged_comp["Rent_PSF_Comp"], name=f"Rent PSF ({year_beta})", marker_color="#FF7F0E", width=0.2, offsetgroup=1))
        
        fig_compare.update_layout(template="plotly_white", barmode="group", yaxis_title="Unit Financial Metric Scale (₹ / Sq. Ft.)", xaxis_tickangle=-45, height=480)
        st.plotly_chart(fig_compare, use_container_width=True)
        
        st.markdown("#### Performance Matrix Dataset Comparison Ledger")
        compare_matrix = merged_comp[["CMP ID", "Cluster", "Rev_PSF_Base", "Rent_PSF_Base", "Rev_PSF_Comp", "Rent_PSF_Comp"]].copy()
        
        # Conditional formatting applied to automatically spotlight maximum yield and risk boundaries
        styled_compare = compare_matrix.style.format({
            "Rev_PSF_Base": "₹{:.2f}", "Rent_PSF_Base": "₹{:.2f}",
            "Rev_PSF_Comp": "₹{:.2f}", "Rent_PSF_Comp": "₹{:.2f}"
        }).apply(spotlight_best_performers, subset=["Rev_PSF_Comp"])\
          .apply(spotlight_worst_performers, subset=["Rent_PSF_Comp"])
          
        st.dataframe(styled_compare, use_container_width=True)

# ====================================================================
# TAB 4: INDIVIDUAL WAREHOUSE DRILLDOWN (SAFETY PROTECTED BUILD)
# ====================================================================
with tabs[3]:
    st.subheader("Granular Individual Property Footprint Lifecycle Review")
    
    alphabetical_codes = sorted(df_portfolio["CMP ID"].unique().tolist()) if not df_portfolio.empty else []
    target_wh = st.selectbox("Select Specific Target Facility for Deep-Dive Analysis:", options=alphabetical_codes)
    
    # Reconstruct month tracking trends horizontally from raw matrix columns
    wh_raw_slice = df_raw_original[df_raw_original["CMP ID"] == target_wh]
    
    if wh_raw_slice.empty:
        st.info("📊 No horizontal matrix data tracking sequence found for this asset ID.")
    else:
        # Extract chronological trend vectors directly from wide month layout coordinates
        rev_row_raw = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("rev|revenue|income", na=False)]
        rent_row_raw = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("rent|fixed", na=False)]
        cap_row_raw = wh_raw_slice[wh_raw_slice["Type_Clean"].str.contains("cap|capacity|space", na=False)]
        
        rev_trend_vals = [float(rev_row_raw[m].iloc[0]) if not rev_row_raw.empty else 0.0 for m in chronological_months]
        rent_trend_vals = [float(rent_row_raw[m].iloc[0]) if not rent_row_raw.empty else 0.0 for m in chronological_months]
        cap_trend_vals = [float(cap_row_raw[m].iloc[0]) if not cap_row_raw.empty else 0.0 for m in chronological_months]
        
        # FIXED: Enforce a defensive check to prevent plotting ValueError crashes on completely empty assets
        if sum(rev_trend_vals) == 0 and sum(rent_trend_vals) == 0 and sum(cap_trend_vals) == 0:
            st.info(f"ℹ️ Selected property `{target_wh}` has zero active records or footprint tracking logged in the spreadsheet rows.")
        else:
            # Interactive dual-axis timeline chart showing dehire curves cleanly
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=chronological_months, y=rev_trend_vals, mode='lines+markers', name='Monthly Revenue (₹)', line=dict(color='#2CA02C', width=3)))
            fig_trend.add_trace(go.Scatter(x=chronological_months, y=rent_trend_vals, mode='lines+markers', name='Monthly Rent (₹)', line=dict(color='#D62728', width=2, dash='dot')))
            fig_trend.add_trace(go.Scatter(x=chronological_months, y=cap_trend_vals, mode='lines+markers', name='Storage Footprint (MT)', line=dict(color='#1F77B4', width=2), yaxis='y2'))
            
            fig_trend.update_layout(
                template="plotly_white",
                title=f"Continuous Month-by-Month Sequence Analytics Vector: {target_wh}",
                yaxis=dict(title="Financial Scale Value (₹)", titlefont=dict(color="#2CA02C"), tickfont=dict(color="#2CA02C")),
                yaxis2=dict(title="Active Capacity Scale (MT)", titlefont=dict(color="#1F77B4"), tickfont=dict(color="#1F77B4"), overlaying='y', side='right'),
                height=380,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
    st.markdown("#### Annual Macro Allocation Accounting Spread")
    
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
        
        # CRITICAL STYLING RULE: Target only the numeric columns explicitly when configuring styling templates
        fmt_target = {col: "₹{:,.0f}" for col in df_history_grid.columns}
        st.dataframe(df_history_grid.style.format(fmt_target), use_container_width=True)
    else:
        st.info("No annual records compiled for this specific facility identifier.")
