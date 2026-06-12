import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Warehouse Analytics", layout="wide")

# 1. File Upload (The easiest way to swap data)
uploaded_file = st.sidebar.file_uploader("Upload Data", type=["csv", "xlsx"])
if not uploaded_file:
    st.info("Please upload your data file in the sidebar.")
    st.stop()

# 2. Data Engine
@st.cache_data
def load_data(file):
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df_raw = load_data()

# 3. Tabs
tabs = st.tabs(["📈 Portfolio Summary", "🔄 YoY Rent", "📊 Compare", "🔍 Individual Drilldown"])

# 4. Tab 4: Drilldown (The Fix)
with tabs[3]:
    st.subheader("Individual Warehouse Drilldown")
    target_wh = st.selectbox("Select Facility:", options=sorted(df_raw["CMP ID"].unique()))
    wh_slice = df_raw[df_raw["CMP ID"] == target_wh]
    
    # Extract only numeric date columns
    date_cols = [c for c in wh_slice.columns if any(x in c for x in ["2023", "2024", "2025", "2026"])]
    
    if not wh_slice.empty and len(date_cols) > 0:
        fig = go.Figure()
        # Add traces safely
        fig.add_trace(go.Scatter(x=date_cols, y=wh_slice[date_cols].iloc[0], name="Values"))
        
        # DEFENSIVE LAYOUT UPDATE
        try:
            fig.update_layout(
                title=f"Trends for {target_wh}",
                yaxis=dict(title="Value"),
                height=400,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render chart: {e}")
    else:
        st.warning("No data found for this selection.")
