import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed – Interactive Dashboard",
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
# Apply Filters
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
# KPI CALCULATION (PLAN / ACTUAL / DIFF)
# ======================================
plan_order = filtered_df["Speed Plan"].notna().sum()
actual_order = filtered_df["Actual Speed"].notna().sum()

plan_minute = int(filtered_df["เวลา Plan"].sum() / 60) if "เวลา Plan" in filtered_df else 0
actual_minute = int(filtered_df["เวลา Actual"].sum() / 60) if "เวลา Actual" in filtered_df else 0

diff_order = actual_order - plan_order
diff_minute = actual_minute - plan_minute

# ======================================
# STOP TIME KPI (เวลาหยุดเครื่อง)
# ======================================
stop_df = filtered_df[
    filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง"
]

stop_order = len(stop_df)

stop_minute = (
    int(stop_df["เวลาหยุดข้อมูลเครื่อง"].sum())
    if "เวลาหยุดข้อมูลเครื่อง" in stop_df
    else 0
)

# ======================================
# KPI DISPLAY
# ======================================
st.markdown("## 📊 Speed – Interactive Dashboard")

def kpi_card(title, bg_color, order, minute, text_color="#000"):
    return f"""
    <div style="
        background:{bg_color};
        padding:20px;
        border-radius:18px;
        color:{text_color};
        box-shadow:0 6px 18px rgba(0,0,0,0.15);
    ">
        <h2 style="text-align:center;margin-bottom:16px">{title}</h2>
        <div style="display:flex;gap:14px;justify-content:center">
            <div style="
                background:rgba(255,255,255,0.35);
                padding:12px 18px;
                border-radius:12px;
                min-width:120px;
                text-align:center;
            ">
                <div style="font-size:14px;opacity:0.8">Order</div>
                <div style="font-size:26px;font-weight:700">{order:,}</div>
            </div>
            <div style="
                background:rgba(255,255,255,0.35);
                padding:12px 18px;
                border-radius:12px;
                min-width:120px;
                text-align:center;
            ">
                <div style="font-size:14px;opacity:0.8">Minute</div>
                <div style="font-size:26px;font-weight:700">{minute:+,}</div>
            </div>
        </div>
    </div>
    """

col_plan, col_actual, col_stop, col_diff = st.columns(4)

with col_plan:
    st.markdown(
        kpi_card(
            "PLAN",
            "#2ec4c6",
            plan_order,
            int(plan_minute)
        ),
        unsafe_allow_html=True
    )

with col_actual:
    st.markdown(
        kpi_card(
            "ACTUAL",
            "#a3d977",
            actual_order,
            int(actual_minute)
        ),
        unsafe_allow_html=True
    )
    
with col_stop:
    st.markdown(
        f"""
        <div style="
            background:#ffb703;
            padding:20px;
            border-radius:18px;
            color:#000;
            box-shadow:0 6px 18px rgba(0,0,0,0.15);
        ">
            <h2 style="text-align:center;margin-bottom:16px">
                STOP TIME
            </h2>
            <div style="display:flex;gap:14px;justify-content:center">
                <div style="
                    background:rgba(255,255,255,0.45);
                    padding:12px 18px;
                    border-radius:12px;
                    min-width:120px;
                    text-align:center;
                ">
                    <div style="font-size:14px;opacity:0.8">
                        Order (จอดเครื่อง)
                    </div>
                    <div style="font-size:26px;font-weight:700">
                        {stop_order:,}
                    </div>
                </div>
                <div style="
                    background:rgba(255,255,255,0.45);
                    padding:12px 18px;
                    border-radius:12px;
                    min-width:120px;
                    text-align:center;
                ">
                    <div style="font-size:14px;opacity:0.8">
                        Minute
                    </div>
                    <div style="font-size:26px;font-weight:700">
                        {stop_minute:,}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# สี DIFF ตามค่า
diff_color = "#ff3b30" if diff_order < 0 or diff_minute < 0 else "#2ecc71"

with col_diff:
    st.markdown(
        kpi_card(
            "DIFF",
            diff_color,
            diff_order,
            int(diff_minute),
            text_color="white"
        ),
        unsafe_allow_html=True
    )

st.divider()

# ======================================
# Charts
# ======================================
colA, colB = st.columns(2)

with colA:
    st.subheader("📊 สัดส่วนลักษณะ Order ความยาว (100%) แยกตามเครื่องจักร")

    # นับจำนวน Order
    bar_df = (
        filtered_df
        .groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"])
        .size()
        .reset_index(name="Order Count")
    )

    # คำนวณ % ต่อเครื่อง
    bar_df["Percent"] = (
        bar_df
        .groupby("เครื่องจักร")["Order Count"]
        .transform(lambda x: x / x.sum() * 100)
    )

    # สร้าง label = จำนวน + %
    bar_df["Label"] = (
        bar_df["Order Count"].astype(str)
        + "<br>("
        + bar_df["Percent"].round(1).astype(str)
        + "%)"
    )

    fig_bar = px.bar(
        bar_df,
        x="Percent",
        y="เครื่องจักร",
        color="ลักษณะ Order ความยาว",
        orientation="h",
        text="Label",
        title="100% Stacked: ลักษณะ Order ความยาว แยกตามเครื่องจักร"
    )

    fig_bar.update_layout(
        barmode="stack",
        xaxis_title="สัดส่วน (%)",
        yaxis_title="เครื่องจักร",
        legend_title_text="ลักษณะ Order ความยาว",
        height=420,
        xaxis=dict(range=[0, 100])
    )

    fig_bar.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont_size=14
    )

    st.plotly_chart(fig_bar, use_container_width=True)

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
