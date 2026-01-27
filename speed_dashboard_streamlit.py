import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed & งานขาดจำนวน – Interactive Dashboard",
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
    return pd.read_csv(url)

df = load_data()

# ======================================
# Clean column names
# ======================================
df.columns = df.columns.str.strip()

# ======================================
# Convert Date / Time
# ======================================
df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")
df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
df["Stop Time"] = pd.to_datetime(df["Stop Time"], errors="coerce")

# ======================================
# Default Date = 7 days latest with data
# ======================================
max_date = df["วันที่"].max()
min_7days = max_date - pd.Timedelta(days=6)

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

date_range = st.sidebar.date_input(
    "📅 เลือกช่วงวันที่",
    [min_7days, max_date]
)

def multi_filter(label, col):
    return st.sidebar.multiselect(
        label,
        sorted(df[col].dropna().unique())
    )

machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
shifts = multi_filter("⏱ กะ", "กะ")
speed_status = multi_filter("📊 Speed เทียบแผน", "Speed เทียบแผน")
stop_types = multi_filter("🛑 ลักษณะเวลาหยุดเครื่อง", "ลักษณะ เวลาหยุดเครื่อง")
order_lengths = multi_filter("📦 ลักษณะ Order ความยาว", "ลักษณะ Order ความยาว")

# ======================================
# Apply Filters (ว่าง = ไม่ filter)
# ======================================
filtered_df = df[
    (df["วันที่"] >= pd.to_datetime(date_range[0])) &
    (df["วันที่"] <= pd.to_datetime(date_range[1]))
]

if machines:
    filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(machines)]

if shifts:
    filtered_df = filtered_df[filtered_df["กะ"].isin(shifts)]

if speed_status:
    filtered_df = filtered_df[filtered_df["Speed เทียบแผน"].isin(speed_status)]

if stop_types:
    filtered_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"].isin(stop_types)]

if order_lengths:
    filtered_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"].isin(order_lengths)]

# ======================================
# Helper functions
# ======================================
def safe_mean(series):
    return series.mean() if len(series) > 0 else 0

def safe_percent_under(df):
    if len(df) == 0:
        return 0
    return (df["Actual Speed"] < df["Speed Plan"]).mean() * 100

# ======================================
# KPI Section
# ======================================
st.title("📉 Speed & งานขาดจำนวน – Interactive Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric("จำนวน Order", f"{len(filtered_df):,}")
c2.metric("Speed Actual เฉลี่ย", f"{safe_mean(filtered_df['Actual Speed']):.2f}")
c3.metric("Speed Plan เฉลี่ย", f"{safe_mean(filtered_df['Speed Plan']):.2f}")
c4.metric("% ต่ำกว่าแผน", f"{safe_percent_under(filtered_df):.1f}%")

st.divider()

# ======================================
# Charts
# ======================================
colA, colB = st.columns(2)

with colA:
    trend = (
        filtered_df
        .groupby("วันที่", as_index=False)
        .agg(
            Speed_Actual=("Actual Speed", "mean"),
            Speed_Plan=("Speed Plan", "mean")
        )
    )

    fig_line = px.line(
        trend,
        x="วันที่",
        y=["Speed_Actual", "Speed_Plan"],
        markers=True,
        title="📈 Speed Actual vs Plan"
    )
    st.plotly_chart(fig_line, use_container_width=True)

with colB:
    stop_sum = (
        filtered_df
        .groupby("ลักษณะ เวลาหยุดเครื่อง", as_index=False)
        .size()
        .rename(columns={"size": "จำนวนครั้ง"})
    )

    fig_pie = px.pie(
        stop_sum,
        names="ลักษณะ เวลาหยุดเครื่อง",
        values="จำนวนครั้ง",
        hole=0.45,
        title="🛑 สัดส่วนลักษณะเวลาหยุดเครื่อง"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ======================================
# Detail Table
# ======================================
st.subheader("📋 รายละเอียด Order")

show_cols = [
    "วันที่",
    "เครื่องจักร",
    "กะ",
    "Speed Plan",
    "Actual Speed",
    "Speed เทียบแผน",
    "ลักษณะ Order ความยาว",
    "ลักษณะ เวลาหยุดเครื่อง",
    "รายละเอียด",
    "Start Time",
    "Stop Time"
]

st.dataframe(
    filtered_df[show_cols].sort_values("วันที่", ascending=False),
    use_container_width=True,
    height=520
)
