import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="Maintenance Executive Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# =========================================================
# Google Sheets Config
# =========================================================
SHEET_ID = "1tWy2VQSaDTqVB04w8KEKlK7RTIVPLdgnCmysPabFS0g"
SHEET_NAME = "รายงาน ประจำวัน"

# =========================================================
# Load Data
# =========================================================
@st.cache_data(ttl=300)
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
        df.get("เวลาหยุดเครื่อง Actual", 0), errors="coerce"
    ).fillna(0)

    df["จำนวนครั้งที่หยุด Actual"] = pd.to_numeric(
        df.get("จำนวนครั้งที่หยุด Actual", 0), errors="coerce"
    ).fillna(0)

    return df

df = load_data()

# =========================================================
# Sidebar Filters (Executive Control)
# =========================================================
st.sidebar.header("🔎 ตัวกรองข้อมูล (Executive Control)")

start_date, end_date = st.sidebar.date_input(
    "📅 ช่วงวันที่",
    [df["วันที่"].min(), df["วันที่"].max()]
)

station_filter = st.sidebar.multiselect(
    "🧩 Station",
    sorted(df["Station"].dropna().unique())
)

job_filter = st.sidebar.multiselect(
    "🛠️ ประเภทงาน",
    sorted(df["ประเภทงาน"].dropna().unique())
)

# =========================================================
# Apply Filters
# =========================================================
fdf = df[
    (df["วันที่"] >= pd.to_datetime(start_date)) &
    (df["วันที่"] <= pd.to_datetime(end_date))
]

if station_filter:
    fdf = fdf[fdf["Station"].isin(station_filter)]

if job_filter:
    fdf = fdf[fdf["ประเภทงาน"].isin(job_filter)]

# =========================================================
# ① Executive KPI
# =========================================================
st.markdown("# 📌 Executive Maintenance Dashboard")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "⏱️ Downtime รวม (นาที)",
        f"{fdf['เวลาหยุดเครื่อง Actual'].sum():,.0f}"
    )

with k2:
    st.metric(
        "🔴 จำนวนครั้งหยุด",
        f"{fdf['จำนวนครั้งที่หยุด Actual'].sum():,.0f}"
    )

station_sum = (
    fdf.groupby("Station")["เวลาหยุดเครื่อง Actual"]
    .sum()
    .sort_values(ascending=False)
)

with k3:
    st.metric(
        "⚠️ Station ปัญหาหลัก",
        station_sum.index[0] if len(station_sum) > 0 else "-"
    )

with k4:
    st.metric(
        "📅 ช่วงข้อมูล",
        f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    )

# =========================================================
# ② Pareto – Key Loss Driver
# =========================================================
st.markdown("## 📊 Key Loss Driver : Pareto ตาม Station")

pareto_df = (
    fdf.groupby("Station")
    .agg(
        downtime_minutes=("เวลาหยุดเครื่อง Actual", "sum"),
        downtime_count=("จำนวนครั้งที่หยุด Actual", "sum")
    )
    .reset_index()
    .sort_values("downtime_minutes", ascending=False)
    .head(10)
)

pareto_df["rank"] = range(1, len(pareto_df) + 1)
pareto_df["group"] = pareto_df["rank"].apply(
    lambda x: "Top 3" if x <= 3 else "Others"
)

pareto_df["label"] = (
    pareto_df["downtime_minutes"].astype(int).astype(str)
    + " นาที ("
    + pareto_df["downtime_count"].astype(int).astype(str)
    + " ครั้ง)"
)

pareto_df = pareto_df.iloc[::-1]

fig_pareto = px.bar(
    pareto_df,
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

fig_pareto.update_traces(textposition="inside", insidetextanchor="end")
fig_pareto.update_layout(
    xaxis_title="เวลาหยุดเครื่อง (นาที)",
    yaxis_title="Station",
    legend_title_text="กลุ่ม Station"
)

st.plotly_chart(fig_pareto, use_container_width=True)

st.caption("🔍 *โฟกัส Station สีแดงก่อน จะลด Downtime ได้เร็วที่สุด*")

# =========================================================
# ③ Trend – Time Based Decision
# =========================================================
st.markdown("## 📈 แนวโน้ม Downtime & จำนวนครั้งหยุด")

period = st.selectbox(
    "เลือกรูปแบบแนวโน้ม",
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
    text_auto=True,
    labels={"downtime_minutes": "Downtime (นาที)"}
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
    yaxis=dict(title="Downtime (นาที)"),
    yaxis2=dict(
        title="จำนวนครั้งหยุด",
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h", y=1.02)
)

st.plotly_chart(fig_trend, use_container_width=True)

# =========================================================
# ④ Recent Critical Jobs (Executive Table)
# =========================================================
st.markdown("## 📋 งานซ่อมบำรุงที่กระทบล่าสุด")

display_df = fdf.copy()
display_df = display_df.sort_values("วันที่", ascending=False)
display_df["วันที่"] = display_df["วันที่"].dt.strftime("%d/%m/%Y")

st.dataframe(
    display_df[
        [
            "วันที่",
            "Station",
            "ประเภทงาน",
            "ปัญหา ความขัดข้องที่เกิด",
            "เวลาหยุดเครื่อง Actual",
            "จำนวนครั้งที่หยุด Actual",
        ]
    ].head(10),
    use_container_width=True
)
