import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Operations Data Desk")
st.title("🏢 Warehouse Performance Portal")
st.markdown("Track rent costs, revenue streams, and asset efficiency across multi-year milestones.\n---")

@st.cache_data
def load_data():
    raw = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="RAW Data", engine="openpyxl")
    raw["CMP ID"] = raw["CMP ID"].astype(str).str.strip().str.upper()
    raw["Details"] = raw["Details"].astype(str).str.strip()
    for y in ["FY 23-24", "FY 24-25", "FY 25-26"]:
        if y in raw.columns:
            raw[y] = pd.to_numeric(raw[y], errors='coerce').fillna(0)
    rent = pd.read_excel("Rent Analysis Data.xlsx", sheet_name="Rent Data", skiprows=1, engine="openpyxl")
    return raw, rent

try:
    df_raw, df_rent_details = load_data()
except Exception as e:
    st.error(f"⚠️ Error loading data: {e}"); st.stop()

# SIDEBAR CONTROL FILTERS
st.sidebar.header("🎛️ Page Filters")
selected_fy = st.sidebar.selectbox("Select Target Fiscal Year (Tab 1)", ["FY 23-24", "FY 24-25", "FY 25-26"], index=1)
min_c, max_c = int(df_raw["Capacity"].min()), int(df_raw["Capacity"].max())
s_cap = st.sidebar.slider("Filter by Warehouse Capacity (MT)", min_c, max_c, (min_c, max_cap))

df_f_raw = df_raw[(df_raw["Capacity"] >= s_cap[0]) & (df_raw["Capacity"] <= s_cap[1])]

t1, t2, t3, t4 = st.tabs(["📈 Portfolio Performance Summary", "🔄 YoY Sq. Ft. Rent Analyzer", "📊 Compare Two Years", "🔍 Individual Warehouse Drilldown"])

# TAB 1: PORTFOLIO SUMMARY
with t1:
    st.header("📌 Macro Financial & Spatial Summary")
    rent_tot = df_f_raw[df_f_raw["Details"] == "Rent"][selected_fy].sum()
    rev_tot = df_f_raw[df_f_raw["Details"] == "Rev"][selected_fy].sum()
    net_surp = rev_tot - rent_tot
    r_to_r = (rent_tot / rev_tot * 100) if rev_tot > 0 else 0
    sqft_tot = df_f_raw.drop_duplicates(subset=["CMP ID"])["Capacity"].sum() * 6
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 Total Revenue", f"₹{rev_tot:,.0f}")
    m2.metric("📉 Total Fixed Rent", f"₹{rent_tot:,.0f}")
    m3.metric("🏛️ Net Contribution Surplus", f"₹{net_surp:,.0f}")
    m4.metric("📊 Rent-to-Revenue Ratio", f"{r_to_r:.1f}%")
    
    st.markdown("#### 📐 Spatial Unit Rate Performance Metrics")
    s1, s2, s3 = st.columns(3)
    s1.metric("🏢 Total Area Leased", f"{sqft_tot:,.0f} Sq. Ft.")
    s2.metric("🟢 Macro Revenue / Sq. Ft.", f"₹{(rev_tot/sqft_tot if sqft_tot > 0 else 0):.2f}/sqft")
    s3.metric("🔴 Macro Rent / Sq. Ft.", f"₹{(rent_tot/sqft_tot if sqft_tot > 0 else 0):.2f}/sqft")
    
    st.markdown("---")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.subheader("🏆 Top 10 Revenue Generating Clusters")
        fig = px.bar(df_f_raw[df_f_raw["Details"] == "Rev"].nlargest(10, selected_fy), x=selected_fy, y="CMP ID", orientation='h', color_continuous_scale="Viridis")
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c_col2:
        st.subheader("🎯 Overhead Efficiency Scatter Profiler")
        pv = df_f_raw.pivot_table(index=["CMP ID", "Capacity"], columns="Details", values=selected_fy).reset_index()
        if "Rent" in pv.columns and "Rev" in pv.columns:
            st.plotly_chart(px.scatter(pv, x="Rent", y="Rev", size="Capacity", hover_name="CMP ID", color="Rev", color_continuous_scale="RdYlGn", trendline="ols"), use_container_width=True)

# TAB 2: YoY SQ FT RENT ANALYZER
with t2:
    st.header("📐 Per Square Foot (PSF) Lease Cost Tracking")
    st.markdown("Monitor YoY real estate spatial efficiency for assets active for at least two years.")
    yrs = ["FY 23-24", "FY 24-25", "FY 25-26"]
    sum_df = df_raw.groupby(["CMP ID", "Capacity", "Details"])[yrs].sum().reset_index()
    sum_df["Act_Count"] = (sum_df["FY 23-24"] > 0).astype(int) + (sum_df["FY 24-25"] > 0).astype(int) + (sum_df["FY 25-26"] > 0).astype(int)
    s_rent = sum_df[(sum_df["CMP ID"].isin(sum_df[sum_df["Act_Count"] >= 2]["CMP ID"].unique())) & (sum_df["Details"] == "Rent")].copy()
    
    if not s_rent.empty:
        s_rent["Est_SqFt"] = s_rent["Capacity"] * 6
        for y in yrs: s_rent[f"{y}_PSF"] = s_rent[y] / s_rent["Est_SqFt"]
        sel_w = st.multiselect("🔍 Search and Select Specific Warehouses to Display:", options=sorted(list(s_rent["CMP ID"].unique())))
        disp_df = s_rent[s_rent["CMP ID"].isin(sel_w)].copy() if sel_w else s_rent.copy()
        
        m_psf = disp_df.melt(id_vars=["CMP ID", "Capacity", "Est_SqFt"], value_vars=[f"{y}_PSF" for y in yrs], var_name="Fiscal Year", value_name="Rent PSF")
        m_psf["Fiscal Year"] = m_psf["Fiscal Year"].apply(lambda x: x.split('_')[0])
        
        st.plotly_chart(px.bar(m_psf, x="CMP ID", y="Rent PSF", color="Fiscal Year", barmode="group", title="Year-on-Year Rent Cost per Square Foot (1 MT = 6 Sq. Ft.)", color_discrete_map={"FY 23-24": "#2CA02C", "FY 24-25": "#FFD700", "FY 25-26": "#D62728"}), use_container_width=True)
        st.subheader("📊 Spatial Efficiency Ledger")
        st.dataframe(disp_df[["CMP ID", "Capacity", "Est_SqFt", "FY 23-24_PSF", "FY 24-25_PSF", "FY 25-26_PSF"]].style.format({"Capacity": "{:,.0f} MT", "Est_SqFt": "{:,.0f} Sq. Ft.", "FY 23-24_PSF": "₹{:.2f}/sf", "FY 24-25_PSF": "₹{:.2f}/sf", "FY 25-26_PSF": "₹{:.2f}/sf"}), use_container_width=True)
    else: st.info("No long-term operational facilities found matching benchmarks.")

# TAB 3: DUAL-YEAR COMPARE TWO YEARS
with t3:
    st.header("📊 Comparative Dual-Period Unit Assessment")
    c1, c2 = st.columns(2)
    b_yr = c1.selectbox("Select Baseline Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=0)
    c_yr = c2.selectbox("Select Comparison Year", ["FY 23-24", "FY 24-25", "FY 25-26"], index=2)
    
    if b_yr == c_yr: st.warning("Please choose two different fiscal periods.")
    else:
        p_sum = df_raw.groupby(["CMP ID", "Capacity", "Details"])[[b_yr, c_yr]].sum().reset_index()
        p_seasoned = p_sum[p_sum["CMP ID"].isin(p_sum[(p_sum["Details"] == "Rev") & ((p_sum[b_yr] > 0) | (p_sum[c_yr] > 0))]["CMP ID"].unique())].copy()
        if not p_seasoned.empty:
            p_seasoned["SqFt"] = p_seasoned["Capacity"] * 6
            c_pv = p_seasoned.pivot_table(index=["CMP ID", "SqFt"], columns="Details", values=[b_yr, c_yr]).reset_index()
            for k in [b_yr, c_yr]:
                if (k, "Rev") not in c_pv.columns: c_pv[(k, "Rev")] = 0
                if (k, "Rent") not in c_pv.columns: c_pv[(k, "Rent")] = 0
            c_pv["B_Rev"] = c_pv[(b_yr, "Rev")] / c_pv["SqFt"]; c_pv["B_Rent"] = c_pv[(b_yr, "Rent")] / c_pv["SqFt"]
            c_pv["C_Rev"] = c_pv[(c_yr, "Rev")] / c_pv["SqFt"]; c_pv["C_Rent"] = c_pv[(c_yr, "Rent")] / c_pv["SqFt"]
            
            sel_comp = st.multiselect("🔍 Filter Comparison Visualizer by Facility Code:", options=sorted(list(c_pv["CMP ID"].unique())), key="t3_f")
            plot_pv = c_pv[c_pv["CMP ID"].isin(sel_comp)].copy() if sel_comp else c_pv.copy()
            
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(x=plot_pv["CMP ID"], y=plot_pv["B_Rev"], name=f"{b_yr} Rev/SqFt", marker_color="#00CC96", offsetgroup=1))
            fig_c.add_trace(go.Bar(x=plot_pv["CMP ID"], y=plot_pv["B_Rent"], name=f"{b_yr} Rent/SqFt", marker_color="#EF553B", offsetgroup=1, width=0.2))
            fig_c.add_trace(go.Bar(x=plot_pv["CMP ID"], y=plot_pv["C_Rev"], name=f"{c_yr} Rev/SqFt", marker_color="#0068C9", offsetgroup=2))
            fig_c.add_trace(go.Bar(x=plot_pv["CMP ID"], y=plot_pv["C_Rent"], name=f"{c_yr} Rent/SqFt", marker_color="#FF4B4B", offsetgroup=2, width=0.2))
            fig_c.update_layout(barmode="group", xaxis_title="Warehouse Code", yaxis_title="Value (₹/Sq. Ft.)", legend_orientation="h")
            st.plotly_chart(fig_c, use_container_width=True)
            
            ld = pd.DataFrame({"CMP ID": c_pv["CMP ID"], "Total Area": c_pv["SqFt"], f"{b_yr} Rev/PSF": c_pv["B_Rev"], f"{b_yr} Rent/PSF": c_pv["B_Rent"], f"{c_yr} Rev/PSF": c_pv["C_Rev"], f"{c_yr} Rent/PSF": c_pv["C_Rent"]})
            if sel_comp: ld = ld[ld["CMP ID"].isin(sel_comp)]
            st.dataframe(ld.style.format({"Total Area": "{:,.0f} Sq. Ft.", f"{b_yr} Rev/PSF": "₹{:.2f}/sf", f"{b_yr} Rent/PSF": "₹{:.2f}/sf", f"{c_yr} Rev/PSF": "₹{:.2f}/sf", f"{c_yr} Rent/PSF": "₹{:.2f}/sf"}), use_container_width=True)
        else: st.info("No active locations recorded across target timelines.")

# TAB 4: INDIVIDUAL WAREHOUSE DRILLDOWN
with t4:
    st.header("🔍 Granular Asset Investigation Desk")
    selected_facility = st.selectbox("Select Target Facility to Inspect", sorted(df_raw["CMP ID"].unique()))
    facility_profile = df_raw[df_raw["CMP ID"] == selected_facility]
    m_cols = [c for c in df_raw.columns if any(y in str(c) for y in ["2023", "2024", "2025", "2026"])]
    
    if not facility_profile.empty and len(m_cols) > 0:
        st.metric("Storage Volume Capacity (MT)", f"{facility_profile['Capacity'].values[0]:,} MT")
        t_df = facility_profile.melt(id_vars=["Details"], value_vars=m_cols, var_name="Month", value_name="Amount")
        t_df["Month"] = pd.to_datetime(t_df["Month"])
        t_df = t_df.sort_values("Month")
        st.plotly_chart(px.line(t_df, x="Month", y="Amount", color="Details", markers=True, color_discrete_map={"Rent": "#EF553B", "Rev": "#00CC96"}), use_container_width=True)
        
        st.markdown("### 📊 Annual Consolidated Summary Ledger")
        ann = facility_profile[["Details"] + ["FY 23-24", "FY 24-25", "FY 25-26"]].copy().set_index("Details")
        if "Rev" in ann.index and "Rent" in ann.index: 
            ann.loc["Net Margin surplus"] = ann.loc["Rev"] - ann.loc["Rent"]
            
        # FIXED: Explicitly target only the numerical columns for formatting, leaving strings safe!
        fmt_target = {"FY 23-24": "₹{:,.0f}", "FY 24-25": "₹{:,.0f}", "FY 25-26": "₹{:,.0f}"}
        st.dataframe(ann.style.format(fmt_target), use_container_width=True)
