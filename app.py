import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 1. Load Data
uploaded_file = st.sidebar.file_uploader("Upload Data", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Upload file in sidebar.")
    st.stop()

df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
df.columns = [str(c).strip() for c in df.columns]

# 2. Year-on-Year Engine
# We group the columns by their year/FY keyword
def get_fy_data(df):
    fy_groups = {
        "FY 23-24": [c for c in df.columns if "2023" in str(c) or "2024-01" in str(c)],
        "FY 24-25": [c for c in df.columns if "2024" in str(c) and "2024-01" not in str(c)],
        "FY 25-26": [c for c in df.columns if "2025" in str(c) or "2026" in str(c)]
    }
    
    # We build a new summary DF for YoY comparison
    summary = pd.DataFrame()
    for fy, cols in fy_groups.items():
        # You need to adjust these strings based on your actual column names
        rev_cols = [c for c in cols if "Rev" in c]
        rent_cols = [c for c in cols if "Rent" in c]
        cap_cols = [c for c in cols if "Capacity" in c]
        
        # Calculations: Annualized totals
        summary[f"{fy} Rev"] = df[rev_cols].sum(axis=1)
        summary[f"{fy} Rent"] = df[rent_cols].sum(axis=1)
        # PSF Math: (Total Rent / (Average Capacity * 6))
        avg_cap = df[cap_cols].mean(axis=1)
        summary[f"{fy} Rent PSF"] = summary[f"{fy} Rent"] / (avg_cap * 6)
        summary[f"{fy} Rev PSF"] = summary[f"{fy} Rev"] / (avg_cap * 6)
    return summary

# 3. YoY Rent vs Revenue Comparison (Tab 2)
# Here is how you render the YoY PSF comparison:
st.subheader("YoY Rent vs Revenue Per Sq. Ft.")
summary_df = get_fy_data(df)

# Example: Plotting Rent PSF YoY
fig = go.Figure()
fig.add_trace(go.Bar(name='FY 23-24 Rent PSF', x=df.iloc[:,0], y=summary_df['FY 23-24 Rent PSF']))
fig.add_trace(go.Bar(name='FY 24-25 Rent PSF', x=df.iloc[:,0], y=summary_df['FY 24-25 Rent PSF']))
fig.update_layout(barmode='group')
st.plotly_chart(fig, use_container_width=True)
