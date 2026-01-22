# =====================================
# Shortage Dashboard : DATA CHECK
# Executive Version (FULL FILE)
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Shortage Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- Google Sheet Config ----------------
SHEET_ID = "1gW0lw9XS0JYST-P-ZrXoFq0k4n2ZlXu9hOf3A--JV9U"
GID = "1799697899"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# ---------------- Load Data ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()

    df["วันที่"] = pd.to_datetime(
        df["วันที่"],
        dayfirst=True,
        errors="coerce"
    )
    return df

df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 RESET FILTER"):
    st.session_state.clear()
    st.rerun()

date_range = st.sidebar.date_input(
    "เลือกช่วงวันที่",
    [df["วันที่"].min(), df["วันที่"].max()]
)

mc_filter = st.sidebar.multiselect(
    "MC", sorted(df["MC"].dropna().unique())
)

shift_filter = st.sidebar.multiselect(
    "กะ", sorted(df["กะ"].dropna().unique())
)

status_filter = st.sidebar.multiselect(
    "สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique())
)

customer_filter = st.sidebar.multiselect(
    "ชื่อลูกค้า", sorted(df["ชื่อลูกค้า"].dropna().unique())
)

st.sidebar.subheader("📊 แนวโน้มตามช่วงเวลา")
period = st.sidebar.selectbox(
    "เลือกช่วงเวลา",
    ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"]
)

# ---------------- Apply Filters ----------------
fdf = df[
    (df["วันที่"] >= pd.to_datetime(date_range[0])) &
    (df["วันที่"] <= pd.to_datetime(date_range[1]))
]

if mc_filter:
    fdf = fdf[fdf["MC"].isin(mc_filter)]

if shift_filter:
    fdf = fdf[fdf["กะ"].isin(shift_filter)]

if status_filter:
    fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]

if customer_filter:
    fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]

# ---------------- KPI ----------------
k1, k2, k3 = st.columns(3)

order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()

k1.metric("ORDER TOTAL", f"{order_total:,}")
k2.metric("ครบจำนวน", f"{complete_qty:,}")
k3.metric("ขาดจำนวน", f"{short_qty:,}")

st.divider()

# ---------------- TOP 10 + Donut ----------------
left, right = st.columns([2, 1])

with left:
    top10 = (
        fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]
        .groupby("Detail")
        .size()
        .sort_values()
        .tail(10)
        .reset_index(name="จำนวน")
    )

    top10["เปอร์เซ็นต์"] = (top10["จำนวน"] / order_total * 100).round(1)
    top10["label"] = top10["จำนวน"].astype(str) + " (" + top10["เปอร์เซ็นต์"].astype(str) + "%)"

    fig_top10 = px.bar(
        top10,
        x="จำนวน",
        y="Detail",
        orientation="h",
        title="TOP 10 สาเหตุขาดจำนวน (% เทียบ ORDER TOTAL)",
        color="จำนวน",
        color_continuous_scale="Reds",
        text="label"
    )

    threshold = top10["จำนวน"].median()

    fig_top10.update_traces(
        textposition="inside",
        insidetextanchor="end",
        textfont_size=13,
        textfont_color=[
            "black" if v < threshold else "white"
            for v in top10["จำนวน"]
        ]
    )

    fig_top10.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        xaxis_title="จำนวน"
    )

    st.plotly_chart(fig_top10, use_container_width=True)

with right:
    status_df = fdf["สถานะผลิต"].value_counts().reset_index()
    status_df.columns = ["สถานะ", "จำนวน"]

    fig_status = px.pie(
        status_df,
        names="สถานะ",
        values="จำนวน",
        hole=0.6,
        title="สัดส่วนสถานะผลิต",
        color="สถานะ",
        color_discrete_map={
            "ครบจำนวน": "#2e7d32",
            "ขาดจำนวน": "#c62828"
        }
    )

    st.plotly_chart(fig_status, use_container_width=True)

# ---------------- STACKED BAR : จำนวน + % ----------------
st.divider()
st.subheader("📊 เปอร์เซ็นต์ ครบจำนวน / ขาดจำนวน (Stacked)")

trend = fdf.copy()

# ===== เลือกช่วงเวลา =====
if period == "รายวัน":
    trend["ช่วง"] = trend["วันที่"].dt.date

elif period == "รายสัปดาห์":
    iso = trend["วันที่"].dt.isocalendar()
    trend["ช่วง"] = (
        "Week "
        + iso.week.astype(str)
        + " / "
        + iso.year.astype(str)
    )

elif period == "รายเดือน":
    trend["ช่วง"] = trend["วันที่"].dt.to_period("M").astype(str)

elif period == "รายปี":
    trend["ช่วง"] = trend["วันที่"].dt.year.astype(str)

# ===== สรุปจำนวน =====
summary = (
    trend
    .groupby(["ช่วง", "สถานะผลิต"])
    .size()
    .reset_index(name="จำนวน")
)

total = summary.groupby("ช่วง")["จำนวน"].sum().reset_index(name="รวม")
summary = summary.merge(total, on="ช่วง")

summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / summary["รวม"] * 100).round(1)

summary["label"] = (
    summary["จำนวน"].astype(int).astype(str)
    + " ("
    + summary["เปอร์เซ็นต์"].astype(str)
    + "%)"
)

# ===== บังคับลำดับให้ ครบ อยู่ล่าง / ขาด อยู่บน =====
summary["สถานะผลิต"] = pd.Categorical(
    summary["สถานะผลิต"],
    categories=["ครบจำนวน", "ขาดจำนวน"],
    ordered=True
)

# ===== สร้างกราฟ =====
fig_stack = px.bar(
    summary,
    x="ช่วง",
    y="เปอร์เซ็นต์",
    color="สถานะผลิต",
    text="label",
    barmode="stack",
    category_orders={
        "สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน"]
    },
    color_discrete_map={
        "ครบจำนวน": "#2e7d32",
        "ขาดจำนวน": "#c62828"
    }
)

fig_stack.update_layout(
    yaxis_range=[0, 100],
    yaxis_title="เปอร์เซ็นต์ (%)",
    xaxis_title="ช่วงเวลา",
    legend_title_text="สถานะผลิต"
)

fig_stack.update_traces(
    textposition="inside",
    textfont_size=13
)

st.plotly_chart(fig_stack, use_container_width=True)

# ---------------- Table ----------------
st.divider()
st.subheader("📋 รายละเอียด Order")

st.dataframe(
    fdf.sort_values("วันที่", ascending=False),
    use_container_width=True,
    height=520
)

st.caption("Shortage Dashboard | Executive Version")
