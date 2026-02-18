import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# Page Config & Custom CSS
# ======================================
st.set_page_config(
    page_title="Executive Speed Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS สำหรับตกแต่งให้ดู Official และสะอาดตา
st.markdown("""
<style>
    /* ปรับ Font และระยะห่าง */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    /* Metric Card Style */
    .kpi-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-left: 5px solid #bdc3c7;
        margin-bottom: 10px;
    }
    .kpi-title {
        color: #7f8c8d;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: #2c3e50;
        font-size: 2rem;
        font-weight: 700;
    }
    .kpi-sub {
        font-size: 0.85rem;
        margin-top: 5px;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f2f6;
        border-radius: 5px;
        color: #2c3e50;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #3498db;
        color: #3498db;
    }
</style>
""", unsafe_allow_html=True)

# ======================================
# Google Sheet Config
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

# ======================================
# Load Data & Cleaning
# ======================================
@st.cache_data(ttl=300)
def load_data():
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    )
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("ไม่พบข้อมูลจาก Google Sheet กรุณาตรวจสอบการเชื่อมต่อ")
    st.stop()

# Clean Data
df.columns = df.columns.str.strip()

# Convert Date
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
     df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
df["Stop Time"] = pd.to_datetime(df["Stop Time"], errors="coerce")

# Convert Numerics
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ======================================
# Sidebar & Filters
# ======================================
st.sidebar.title("⚙️ ตัวกรองข้อมูล")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Date Filter
if df["วันที่"].notna().any():
    max_date = df["วันที่"].max()
    min_7days = max_date - pd.Timedelta(days=6)
else:
    max_date = pd.Timestamp.today()
    min_7days = max_date

date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_7days, max_date])

# Checkbox Filters
def multi_filter(label, col):
    if col in df.columns:
        return st.sidebar.multiselect(label, sorted(df[col].astype(str).unique()))
    return []

machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
shifts = multi_filter("⏱ กะ", "กะ")
order_lengths = multi_filter("📦 ลักษณะ Order", "ลักษณะ Order ความยาว")

# Apply Filters
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["วันที่"] >= pd.to_datetime(date_range[0])) &
        (filtered_df["วันที่"] <= pd.to_datetime(date_range[1]))
    ]

if machines: filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(machines)]
if shifts: filtered_df = filtered_df[filtered_df["กะ"].isin(shifts)]
if order_lengths: filtered_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"].isin(order_lengths)]

# ======================================
# Main Layout
# ======================================
st.title("🏭 Production Speed Dashboard")
st.markdown(f"**ข้อมูลระหว่างวันที่:** {date_range[0].strftime('%d/%m/%Y')} ถึง {date_range[1].strftime('%d/%m/%Y') if len(date_range)>1 else ''} | **จำนวนรายการ:** {len(filtered_df):,} Order")

# Create Tabs
tab1, tab2 = st.tabs(["📊 Executive Summary (ภาพรวม)", "📋 Detailed Data (ข้อมูลดิบ)"])

# ======================================
# TAB 1: EXECUTIVE SUMMARY
# ======================================
with tab1:
    # --- KPI Calculation ---
    total_orders = len(filtered_df)
    
    # Speed Achievement Calculation
    avg_plan_speed = filtered_df[filtered_df["Speed Plan"] > 0]["Speed Plan"].mean() if "Speed Plan" in filtered_df else 0
    avg_actual_speed = filtered_df[filtered_df["Actual Speed"] > 0]["Actual Speed"].mean() if "Actual Speed" in filtered_df else 0
    speed_achievement = (avg_actual_speed / avg_plan_speed * 100) if avg_plan_speed > 0 else 0
    
    # Time Calculation
    run_hours = (filtered_df["เวลา Actual"].sum() / 60) if "เวลา Actual" in filtered_df else 0
    plan_hours = (filtered_df["เวลา Plan"].sum() / 60) if "เวลา Plan" in filtered_df else 0
    diff_hours = run_hours - plan_hours
    
    # Stop Time
    stop_hours = 0
    if "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns:
        stop_hours = filtered_df["เวลาหยุดข้อมูลเครื่อง"].sum() / 60

    # --- KPI Cards Display ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    def display_card(col, title, value, sub_text, color_border):
        col.markdown(f"""
        <div class="kpi-card" style="border-left: 5px solid {color_border};">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub" style="color: {'green' if '+' in sub_text else 'red' if '-' in sub_text else '#7f8c8d'};">
                {sub_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    display_card(kpi1, "Total Orders", f"{total_orders:,}", "Count", "#3498db") # Blue
    display_card(kpi2, "Speed Achievement", f"{speed_achievement:,.1f}%", f"Actual: {avg_actual_speed:,.0f} / Plan: {avg_plan_speed:,.0f}", "#9b59b6") # Purple
    display_card(kpi3, "Production Hours", f"{run_hours:,.1f} Hrs", f"{diff_hours:+.1f} Hrs vs Plan", "#2ecc71") # Green
    display_card(kpi4, "Stop Time", f"{stop_hours:,.1f} Hrs", "Downtime Loss", "#e74c3c") # Red

    st.markdown("---")

    # --- Charts Row 1 ---
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("📈 Speed Trend: Plan vs Actual (แนวโน้มความเร็ว)")
        if "วันที่" in filtered_df.columns:
            daily_trend = filtered_df.groupby("วันที่")[["Speed Plan", "Actual Speed"]].mean().reset_index()
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=daily_trend["วันที่"], y=daily_trend["Speed Plan"], 
                                        mode='lines', name='Plan Speed', line=dict(color='gray', dash='dash')))
            fig_line.add_trace(go.Scatter(x=daily_trend["วันที่"], y=daily_trend["Actual Speed"], 
                                        mode='lines+markers', name='Actual Speed', line=dict(color='#2ecc71', width=3)))
            fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), hovermode="x unified", legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_line, use_container_width=True)

    with row1_col2:
        st.subheader("🛑 Stop Analysis (สาเหตุหยุด)")
        if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns and "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns:
            stop_df = filtered_df[filtered_df["เวลาหยุดข้อมูลเครื่อง"] > 0]
            if not stop_df.empty:
                stop_grp = stop_df.groupby("ลักษณะ เวลาหยุดเครื่อง")["เวลาหยุดข้อมูลเครื่อง"].sum().reset_index()
                fig_pie = px.donut(stop_grp, values='เวลาหยุดข้อมูลเครื่อง', names='ลักษณะ เวลาหยุดเครื่อง', 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No downtime recorded.")
        else:
            st.warning("No data for stop analysis")

    # --- Charts Row 2 ---
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("📊 Performance by Machine")
        if "เครื่องจักร" in filtered_df.columns and "Speed เทียบแผน" in filtered_df.columns:
            bar_df = filtered_df.groupby(["เครื่องจักร", "Speed เทียบแผน"]).size().reset_index(name="Count")
            fig_bar = px.bar(bar_df, x="Count", y="เครื่องจักร", color="Speed เทียบแผน", orientation="h",
                             color_discrete_map={"เร็วกว่าแผน": "#2ecc71", "ตามแผน": "#3498db", "ช้ากว่าแผน": "#e74c3c", "ยกเลิกเดินงาน": "#95a5a6"})
            fig_bar.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

    with row2_col2:
        st.subheader("📦 Speed vs Order Length")
        if "ลักษณะ Order ความยาว" in filtered_df.columns:
            scatter_df = filtered_df[filtered_df["Actual Speed"] > 0]
            fig_scatter = px.scatter(scatter_df, x="Actual Speed", y="เวลา Actual", color="ลักษณะ Order ความยาว",
                                   title="Correlation: Speed vs Time", color_discrete_sequence=px.colors.qualitative.Prism)
            fig_scatter.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_scatter, use_container_width=True)

# ======================================
# TAB 2: DETAILED DATA TABLE
# ======================================
with tab2:
    st.subheader("📋 รายละเอียดข้อมูล (Detailed Data View)")
    
    # Download Button
    col_dl, col_blank = st.columns([1, 5])
    with col_dl:
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Excel/CSV", csv, "speed_data.csv", "text/csv")

    # Full Columns List (As requested)
    full_cols_list = [
        "วันที่", "เครื่องจักร", "กะ", "ลำดับที่", "PDR", "Flute", 
        "M5", "M4", "M3", "M2", "M1", 
        "หน้ากว้าง (W) PLAN", "ความยาว (L) PLAN", "T", 
        "ความยาวเมตร PLAN", "ความยาวเมตร MC", 
        "Speed Plan", "Actual Speed", "Speed เทียบแผน", 
        "เวลา Plan", "เวลา Actual", "Diff เวลา", 
        "เวลาหยุดเครื่องจากผลิต", "เวลาหยุดข้อมูลเครื่อง", 
        "Checked-1", "Checked-2", "Start Time", "Stop Time", 
        "ลักษณะ Order PLAN", "ลักษณะ Order MC", 
        "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", 
        "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"
    ]
    
    # Filter valid columns
    existing_cols = [c for c in full_cols_list if c in filtered_df.columns]
    
    if existing_cols:
        # Style Dataframe
        display_df = filtered_df[existing_cols].sort_values("วันที่", ascending=False).reset_index(drop=True)
        
        def highlight_status(row):
            color = ''
            if "Speed เทียบแผน" in row.index:
                val = str(row["Speed เทียบแผน"])
                if "ช้ากว่าแผน" in val: color = 'background-color: #fadbd8' # Light Red
                elif "เร็วกว่าแผน" in val: color = 'background-color: #d5f5e3' # Light Green
            return [color] * len(row)
        
        try:
            st.dataframe(
                display_df.style.apply(highlight_status, axis=1)
                .format({"Speed Plan": "{:.0f}", "Actual Speed": "{:.0f}", "เวลา Plan": "{:.0f}", "เวลา Actual": "{:.0f}"}),
                use_container_width=True,
                height=600
            )
        except:
            st.dataframe(display_df, use_container_width=True, height=600)
    else:
        st.warning("ไม่พบข้อมูลคอลัมน์ที่ระบุ")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey; font-size: 0.8rem;'>Dashboard Update: Real-time from Google Sheets</div>", unsafe_allow_html=True)
