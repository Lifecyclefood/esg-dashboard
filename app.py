import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# -----------------------------------
# PAGE SETTINGS
# -----------------------------------
st.set_page_config(
    page_title="ESG Executive Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------
# CUSTOM STYLING
# -----------------------------------
st.markdown("""
    <style>
        .main { background-color: #0f1117; }
        .block-container { padding-top: 1.5rem; }
        .metric-card {
            background: linear-gradient(135deg, #1a1f2e, #16213e);
            border: 1px solid #2a3a5c;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            text-align: center;
        }
        h1 { color: #e8f4f0 !important; }
        h2, h3 { color: #a8d8cc !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------
# TITLE
# -----------------------------------
st.markdown("## 🌍 ESG Executive Reporting Dashboard")
st.markdown("*Sustainability Intelligence for Leadership & Stakeholders*")
st.divider()

# -----------------------------------
# LOAD DATA
# -----------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "emissions_data.csv")

if not os.path.exists(file_path):
    st.error(f"❌ Dataset not found: `{file_path}`")
    st.info("Make sure `emissions_data.csv` is in the same folder as this script.")
    st.stop()

df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# Rename core columns (adjust if your CSV uses different names)
rename_map = {}
if "Year"       in df.columns: rename_map["Year"]       = "year"
if "Region"     in df.columns: rename_map["Region"]     = "region"
if "Total_CO2"  in df.columns: rename_map["Total_CO2"]  = "emissions"
if "Month"      in df.columns: rename_map["Month"]      = "month"
df = df.rename(columns=rename_map)

# Detect scope columns
scope_cols = [c for c in df.columns if c.lower().startswith("scope")]

# -----------------------------------
# SIDEBAR FILTERS
# -----------------------------------
st.sidebar.image("https://img.icons8.com/color/96/leaf.png", width=60)
st.sidebar.title("Dashboard Filters")

# Region filter
if "region" in df.columns:
    regions = df["region"].dropna().unique().tolist()
    selected_regions = st.sidebar.multiselect(
        "🗺️ Region", regions, default=regions
    )
    df = df[df["region"].isin(selected_regions)]

# Year filter
if "year" in df.columns:
    years = sorted(df["year"].dropna().unique().tolist())
    selected_years = st.sidebar.select_slider(
        "📅 Year Range",
        options=years,
        value=(min(years), max(years))
    )
    df = df[df["year"].between(selected_years[0], selected_years[1])]

st.sidebar.divider()
st.sidebar.caption("ESG Dashboard v1.0 · Sustainability Team")

# -----------------------------------
# KPI METRICS ROW
# -----------------------------------
st.subheader("📊 Key Performance Indicators")

total_emissions = df["emissions"].sum() if "emissions" in df.columns else 0
avg_emissions   = df["emissions"].mean() if "emissions" in df.columns else 0
records         = len(df)

# YoY change (if multi-year data exists)
yoy_delta = None
if "year" in df.columns and "emissions" in df.columns:
    yearly_sum = df.groupby("year")["emissions"].sum()
    if len(yearly_sum) >= 2:
        latest   = yearly_sum.iloc[-1]
        previous = yearly_sum.iloc[-2]
        yoy_delta = round(((latest - previous) / previous) * 100, 1)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌐 Total CO₂ Emissions (t)", f"{total_emissions:,.1f}")
with col2:
    st.metric("📉 Avg Emissions / Record", f"{avg_emissions:,.2f}")
with col3:
    delta_str = f"{yoy_delta}% YoY" if yoy_delta is not None else "N/A"
    delta_color = "inverse" if yoy_delta and yoy_delta < 0 else "normal"
    st.metric("📆 YoY Change", delta_str)
with col4:
    st.metric("📁 Data Records", f"{records:,}")

st.divider()

# -----------------------------------
# CHARTS — ROW 1
# -----------------------------------
col_left, col_right = st.columns(2)

# Yearly Trend
with col_left:
    st.subheader("📈 Yearly CO₂ Trend")
    if "year" in df.columns and "emissions" in df.columns:
        yearly = df.groupby("year", as_index=False)["emissions"].sum()
        fig1 = px.area(
            yearly, x="year", y="emissions",
            title="Total CO₂ Emissions Over Time",
            color_discrete_sequence=["#2ecc71"],
            template="plotly_dark"
        )
        fig1.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cce8df"
        )
        fig1.update_traces(line_width=2.5)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Columns `year` and `emissions` not found.")

# Regional Breakdown
with col_right:
    st.subheader("🌏 Emissions by Region")
    if "region" in df.columns and "emissions" in df.columns:
        region_data = df.groupby("region", as_index=False)["emissions"].sum()
        fig2 = px.bar(
            region_data, x="region", y="emissions",
            title="Regional CO₂ Breakdown",
            color="region",
            template="plotly_dark",
            text_auto=".2s"
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            font_color="#cce8df"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Columns `region` and `emissions` not found.")

# -----------------------------------
# CHARTS — ROW 2
# -----------------------------------
col_left2, col_right2 = st.columns(2)

# Monthly Trend
with col_left2:
    st.subheader("📅 Monthly CO₂ Trend")
    month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    month_col = next((c for c in df.columns if c.lower() == "month"), None)
    if month_col and "emissions" in df.columns:
        monthly = df.groupby(month_col, as_index=False)["emissions"].sum()
        monthly[month_col] = pd.Categorical(
            monthly[month_col], categories=month_order, ordered=True
        )
        monthly = monthly.sort_values(month_col)
        fig3 = px.line(
            monthly, x=month_col, y="emissions",
            markers=True,
            title="Monthly CO₂ Pattern",
            color_discrete_sequence=["#3498db"],
            template="plotly_dark"
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cce8df"
        )
        fig3.update_traces(line_width=2.5, marker_size=8)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Column `Month` not found or no emissions data.")

# Scope Breakdown
with col_right2:
    st.subheader("🏭 Scope 1 / 2 / 3 Breakdown")
    if scope_cols and "year" in df.columns:
        scope_data = df.groupby("year", as_index=False)[scope_cols].sum()
        fig4 = px.bar(
            scope_data, x="year", y=scope_cols,
            barmode="stack",
            title="GHG Scope Emissions by Year",
            template="plotly_dark",
            color_discrete_sequence=["#e74c3c","#f39c12","#9b59b6"]
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#cce8df",
            legend_title="Scope"
        )
        st.plotly_chart(fig4, use_container_width=True)
    elif not scope_cols:
        st.info("No Scope columns (Scope1_CO2, Scope2_CO2, Scope3_CO2) found in data.")
    else:
        st.info("Column `year` not found.")

st.divider()

# -----------------------------------
# EMISSIONS INTENSITY (bonus KPI)
# -----------------------------------
if "region" in df.columns and "emissions" in df.columns:
    st.subheader("🔥 Emissions Intensity by Region (Treemap)")
    treemap_data = df.groupby("region", as_index=False)["emissions"].sum()
    fig5 = px.treemap(
        treemap_data, path=["region"], values="emissions",
        title="Regional Emissions Share",
        color="emissions",
        color_continuous_scale="Greens",
        template="plotly_dark"
    )
    fig5.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#cce8df"
    )
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# -----------------------------------
# RAW DATA TABLE
# -----------------------------------
with st.expander("📄 View Raw Dataset"):
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=csv,
        file_name="esg_filtered_data.csv",
        mime="text/csv"
    )

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")
st.caption("🌿 ESG Executive Dashboard · Built with Streamlit · Sustainability Team")