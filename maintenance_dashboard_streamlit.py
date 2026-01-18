import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Maintenance Executive Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# =========================
# Google Sheets Config
# =========================
SHEET_ID = "1tWy2VQSaDTqVB04w8KEKlK7RTIVPLdgnCmysPabFS0g"
SHEET_NAME = "รายงาน ประจำวัน"

# =========================
# Load Data
# =========================
@st.cache_data(ttl=60)
def load_data():
    sheet_name_encoded = quote(SHEET_NAME)
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={sheet_name_encoded}"
    )
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

    df["เวลาหยุดเครื่อง Actual"] = pd.to_numeric(
        df["เวลาหยุดเครื่อง Actual"], errors="coerce"
    ).fillna(0)

    df["จำนวนครั้งที่หยุด Actual"] = pd.to_numeric(
        df["จำนวนครั้งที่หยุด Actual"], errors="coerce"
    ).fillna(0)
    
    df["สถานะ"] = (
    df["สถานะ"]
    .astype(str)
    .str.strip()
    .replace("None", "")
    )
    
    return df


df = load_data()

# =========================
# Sidebar Filters
# =========================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

start_date, end_date = st.sidebar.date_input(
    "📅 เลือกวันที่",
    [df["วันที่"].min(), df["วันที่"].max()]
)

machine = st.sidebar.multiselect(
    "🏭 เครื่องจักร",
    sorted(df["เครื่องจักร"].dropna().unique())
)

station = st.sidebar.multiselect(
    "🧩 Station",
    sorted(df["Station"].dropna().unique())
)

technician = st.sidebar.multiselect(
    "👷 ประเภทช่าง",
    sorted(df["ประเภทช่าง"].dropna().unique())
)

job_type = st.sidebar.multiselect(
    "🛠️ ประเภทงาน",
    sorted(df["ประเภทงาน"].dropna().unique())
)

status = st.sidebar.multiselect(
    "📌 สถานะ",
    sorted(df["สถานะ"].dropna().unique())
)

# =========================
# Apply Filters
# =========================
fdf = df[
    (df["วันที่"] >= pd.to_datetime(start_date)) &
    (df["วันที่"] <= pd.to_datetime(end_date))
]

if machine:
    fdf = fdf[fdf["เครื่องจักร"].isin(machine)]
if station:
    fdf = fdf[fdf["Station"].isin(station)]
if technician:
    fdf = fdf[fdf["ประเภทช่าง"].isin(technician)]
if job_type:
    fdf = fdf[fdf["ประเภทงาน"].isin(job_type)]

# =========================
# Executive Summary
# =========================
st.markdown("# 📌 Executive Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "⏱️ เวลาหยุดเครื่องรวม (นาที)",
        f"{fdf['เวลาหยุดเครื่อง Actual'].sum():,.0f}"
    )

with col2:
    st.metric(
        "🔴 จำนวนครั้งหยุดเครื่อง",
        f"{fdf['จำนวนครั้งที่หยุด Actual'].sum():,.0f}"
    )

station_summary_all = (
    fdf.groupby("Station")["เวลาหยุดเครื่อง Actual"]
    .sum()
    .sort_values(ascending=False)
)

top_station = station_summary_all.index[0] if len(station_summary_all) else "-"

with col3:
    st.metric("⚠️ Station ปัญหาหลัก", top_station)

# =========================
# Pareto Chart
# =========================
st.markdown("## 📊 Pareto เวลาสูญเสีย (แยกตาม Station)")

station_summary = (
    fdf.groupby("Station")
    .agg(
        downtime_minutes=("เวลาหยุดเครื่อง Actual", "sum"),
        downtime_count=("จำนวนครั้งที่หยุด Actual", "sum")
    )
    .reset_index()
    .sort_values("downtime_minutes", ascending=False)
)

station_top10 = station_summary.head(10).copy()
station_top10["rank"] = range(1, len(station_top10) + 1)
station_top10["group"] = station_top10["rank"].apply(
    lambda x: "Top 3" if x <= 3 else "Others"
)

station_top10["label"] = (
    station_top10["downtime_minutes"].astype(int).astype(str)
    + " นาที ("
    + station_top10["downtime_count"].astype(int).astype(str)
    + " ครั้ง)"
)

station_top10 = station_top10.iloc[::-1]

fig_pareto = px.bar(
    station_top10,
    x="downtime_minutes",
    y="Station",
    orientation="h",
    color="group",
    text="label",
    color_discrete_map={
        "Top 3": "#d62728",
        "Others": "#1f77b4"
    }
)

fig_pareto.update_traces(textposition="inside")
fig_pareto.update_layout(
    xaxis_title="เวลาหยุดเครื่อง (นาที)",
    yaxis_title="Station",
    legend_title="กลุ่ม Station"
)

st.plotly_chart(fig_pareto, use_container_width=True)

# =========================
# Trend Analysis
# =========================
st.markdown("## 📈 แนวโน้มเวลาสูญเสีย และจำนวนครั้งหยุดเครื่อง")

period = st.selectbox(
    "เลือกรูปแบบการดูแนวโน้ม",
    ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"]
)

rule_map = {
    "รายวัน": "D",
    "รายสัปดาห์": "W",
    "รายเดือน": "M",
    "รายปี": "Y"
}

trend_df = (
    fdf.set_index("วันที่")
    .resample(rule_map[period])
    .agg(
        downtime_minutes=("เวลาหยุดเครื่อง Actual", "sum"),
        downtime_count=("จำนวนครั้งที่หยุด Actual", "sum")
    )
    .reset_index()
)

fig_trend = px.bar(
    trend_df,
    x="วันที่",
    y="downtime_minutes",
    labels={"downtime_minutes": "เวลาหยุดเครื่อง (นาที)"},
    text_auto=True
)

fig_trend.add_scatter(
    x=trend_df["วันที่"],
    y=trend_df["downtime_count"],
    mode="lines+markers",
    name="จำนวนครั้งหยุด",
    yaxis="y2",
    line=dict(color="#d62728", width=3)
)

fig_trend.update_layout(
    yaxis=dict(title="เวลาหยุดเครื่อง (นาที)"),
    yaxis2=dict(
        title="จำนวนครั้งหยุด",
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h", y=1.02)
)

st.plotly_chart(fig_trend, use_container_width=True)

# =========================
# Detail Table (Date only)
# =========================
st.markdown("## 📋 รายละเอียดงานซ่อมบำรุง")

display_df = fdf.copy()

# เรียงวันที่ล่าสุดอยู่บนสุด
display_df = display_df.sort_values("วันที่", ascending=False)

# แปลงรูปแบบวันที่ (วัน/เดือน/ปี)
display_df["วันที่"] = display_df["วันที่"].dt.strftime("%d/%m/%Y")


st.dataframe(
    display_df[
        [
            "วันที่",
            "เครื่องจักร",
            "Station",
            "ประเภทช่าง",
            "ประเภทงาน",
            "ปัญหา ความขัดข้องที่เกิด",
            "สาเหตุที่ตรวจพบ",
            "การแก้ไข และป้องกัน",
            "เวลาหยุดเครื่อง Actual",
            "จำนวนครั้งที่หยุด Actual",
            "สถานะ",
            "รายการอะไหล่ที่เปลี่ยน",
            "จำนวน",
        ]
    ],
    use_container_width=True
)
