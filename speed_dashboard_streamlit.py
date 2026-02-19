import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed Performance Dashboard",
    page_icon="📉",
    layout="wide"
)

# ======================================
# Google Sheet Config
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

# ======================================
# Load Data
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
    st.warning("ไม่พบข้อมูลในระบบ กรุณาตรวจสอบการเชื่อมต่อ")
    st.stop()

# ======================================
# Data Cleaning (Robust Version)
# ======================================
df.columns = df.columns.str.strip()

# 1. จัดการตัวเลข (Numeric)
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# 2. จัดการข้อความ (Text) - ป้องกันข้อมูลหาย
text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2"]
for col in text_cols:
    if col in df.columns:
        # เก็บค่าเดิมไว้ เปลี่ยนเฉพาะที่เป็น NaN จริงๆ เป็นค่าว่าง
        df[col] = df[col].fillna("").astype(str).str.strip()
        # กรองเฉพาะคำที่เป็นระบบสร้างขึ้นเช่น 'nan' หรือ 'None' ออก
        df[col] = df[col].apply(lambda x: "" if x.lower() in ['nan', 'none'] else x)

# 3. จัดการวันที่ (Date)
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
    df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 รีโหลดข้อมูล"):
    st.cache_data.clear()
    st.rerun()

# Default Date Selection
if df["วันที่"].notna().any():
    max_date = df["วันที่"].max()
    min_7days = max_date - pd.Timedelta(days=6)
else:
    max_date = pd.Timestamp.today()
    min_7days = max_date

date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_7days, max_date])

def create_multi_filter(label, col):
    if col in df.columns:
        opts = sorted([o for o in df[col].unique() if o != ""])
        return st.sidebar.multiselect(label, opts)
    return []

f_machines = create_multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
f_shifts = create_multi_filter("⏱ กะ", "กะ")
f_stop_types = create_multi_filter("🛑 ลักษณะเวลาหยุดเครื่อง", "ลักษณะ เวลาหยุดเครื่อง")

# ======================================
# Filter Logic
# ======================================
if len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    filtered_df = df.copy()

if f_machines: filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(f_machines)]
if f_shifts: filtered_df = filtered_df[filtered_df["กะ"].isin(f_shifts)]
if f_stop_types: filtered_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"].isin(f_stop_types)]

# ======================================
# KPI CALCULATION (With Rounding)
# ======================================

# 1. NON-STOP
ns_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
ns_count = len(filtered_df[ns_mask])
ns_time_raw = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# 2. STOP ORDERS
so_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
so_count = len(filtered_df[so_mask])
so_time_raw = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# 3. OVERALL
overall_time = int(round(ns_time_raw + so_time_raw))

# ======================================
# Dashboard Layout
# ======================================
st.markdown("### 📊 Speed – Performance Overview")

def kpi_card(title, color, order, time, label_o="Order", label_t="Time Min"):
    return f"""
    <div style="background:{color}; padding:20px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">
        <h4 style="text-align:center; margin:0 0 15px 0; font-weight:800; text-transform:uppercase;">{title}</h4>
        <div style="display:flex; gap:10px; justify-content:space-between;">
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                <div style="font-size:12px; opacity:0.9;">{label_o}</div>
                <div style="font-size:24px; font-weight:800;">{order:,}</div>
            </div>
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                <div style="font-size:12px; opacity:0.9;">{label_t}</div>
                <div style="font-size:24px; font-weight:800;">{time:+,}</div>
            </div>
        </div>
    </div>
    """

c1, c2, c3 = st.columns(3)
with c1: st.markdown(kpi_card("NON-STOP", "#8e44ad", ns_count, int(round(ns_time_raw))), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("STOP ORDERS", "#d35400", so_count, int(round(so_time_raw))), unsafe_allow_html=True)
with c3:
    ov_color = "#27ae60" if overall_time >= 0 else "#c0392b"
    st.markdown(kpi_card("OVERALL SPEED", ov_color, ns_count + so_count, overall_time), unsafe_allow_html=True)

st.divider()

# ======================================
# Trend Analysis (ISO Week)
# ======================================
st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (Time Trend)")
trend_df = filtered_df.copy()
trend_df['Val'] = trend_df.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)

freq = st.selectbox("เลือกช่วงเวลา:", ["รายวัน", "รายสัปดาห์", "รายเดือน"])

if freq == "รายสัปดาห์":
    trend_df['ISO_Week'] = trend_df['วันที่'].dt.isocalendar().week
    res = trend_df.groupby('ISO_Week')['Val'].sum().reset_index()
    res['Label'] = res['ISO_Week'].apply(lambda x: f"WEEK {x}")
else:
    mode = {"รายวัน": "D", "รายเดือน": "MS"}
    res = trend_df.set_index('วันที่')['Val'].resample(mode[freq]).sum().reset_index()
    fmt = {"รายวัน": "%d/%m/%Y", "รายเดือน": "%m/%Y"}
    res['Label'] = res['วันที่'].dt.strftime(fmt[freq])

fig_trend = go.Figure(go.Bar(
    x=res['Label'], y=res['Val'],
    marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res['Val']],
    text=res['Val'].round(0).astype(int),
    textposition='outside'
))
fig_trend.update_layout(height=350, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ======================================
# Machine & Order Analysis
# ======================================
ca, cb = st.columns(2)
with ca:
    st.markdown("#### 🏭 สัดส่วนประสิทธิภาพแยกตามเครื่องจักร")
    if "Speed เทียบแผน" in filtered_df.columns:
        bar_data = filtered_df.groupby(["เครื่องจักร", "Speed เทียบแผน"]).size().reset_index(name="Count")
        fig_bar = px.bar(bar_data, x="Count", y="เครื่องจักร", color="Speed เทียบแผน", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_bar.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

with cb:
    st.markdown("#### 🛑 สาเหตุการหยุดเครื่อง")
    if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
        pie_data = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
        fig_pie = px.pie(pie_data, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5)
        fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

# ======================================
# Detailed Data Table
# ======================================
st.divider()
st.subheader("📋 รายละเอียดข้อมูล (Data Logs)")
display_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
existing_cols = [c for c in display_cols if c in filtered_df.columns]
st.dataframe(filtered_df[existing_cols].sort_values("วันที่", ascending=False), use_container_width=True, height=400)
