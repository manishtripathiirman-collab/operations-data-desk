import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. LOAD DATA
uploaded_file = st.sidebar.file_uploader("Upload Warehouse Data", type=["csv", "xlsx"])
if not uploaded_file:
    st.info("Upload your CSV/Excel file in the sidebar to begin.")
    st.stop()

@st.cache_data
def load_and_clean(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = load_and_clean(uploaded_file)

# 2. DATA PREP ENGINE
# Your data columns repeat: [Date] Capacity, [Date] Rent, [Date] Rev
def get_category_cols(category_keyword):
    return [c for c in df.columns if category_keyword in c]

# 3. TABS
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent Analyzer", "📊 Two-Year Comparison", "🔍 Warehouse Drilldown"])

# TAB 1: PORTFOLIO PERFORMANCE
with tabs[0]:
    st.subheader("Portfolio Performance Summary")
    # Spatial Logic: Capacity * 6 = SqFt
    total_mt = df[get_category_cols("Capacity")].sum().sum()
    total_sqft = total_mt * 6
    total_rev = df[get_category_cols("Rev")].sum().sum()
    total_rent = df[get_category_cols("Rent")].sum().sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", f"₹{total_rev:,.0f}")
    c2.metric("Rent", f"₹{total_rent:,.0f}")
    c3.metric("Net Surplus", f"₹{total_rev - total_rent:,.0f}")
    c4.metric("Total Area", f"{total_sqft:,.0f} Sq. Ft.")

# TAB 2: YoY RENT ANALYZER
with tabs[2]: # Using index 2 for the Comparison Tool as requested
    st.subheader("Two-Year Comparison Tool")
    c1, c2 = st.columns(2)
    yr1 = c1.selectbox("Baseline Year", ["2023", "2024", "2025"])
    yr2 = c2.selectbox("Target Year", ["2024", "2025", "2026"])
    
    if yr1 == yr2:
        st.warning("Please select different years for comparison.")
    else:
        # Filter columns for specific years
        y1_rev = df[get_category_cols(yr1 + "-")].filter(like="Rev").sum(axis=1)
        y2_rev = df[get_category_cols(yr2 + "-")].filter(like="Rev").sum(axis=1)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df.iloc[:,0], y=y1_rev, name=yr1))
        fig.add_trace(go.Bar(x=df.iloc[:,0], y=y2_rev, name=yr2))
        fig.update_layout(barmode='group')
        st.plotly_chart(fig, use_container_width=True)

# TAB 4: DRILLDOWN
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target = st.selectbox("Select Warehouse:", df.iloc[:,0].unique())
    slice_df = df[df.iloc[:,0] == target]
    
    if not slice_df.empty:
        # Plot Revenue vs Rent over time
        st.line_chart(slice_df.filter(like="Rev").T)
        st.line_chart(slice_df.filter(like="Rent").T)
