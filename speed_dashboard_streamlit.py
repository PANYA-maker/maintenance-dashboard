import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed Shortage Dashboard",
    page_icon="📉",
    layout="wide"
)

# ======================================
# Google Sheet Config
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

# ======================================
# Load Data from Google Sheet
# ======================================
@st.cache_data(ttl=300)
def load_data():
    sheet_name_encoded = quote(SHEET_NAME)
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={sheet_name_encoded}"
    )
    df = pd.read_csv(url)
    return df

df = load_data()

# ======================================
# Preprocess
# ======================================
df["Date"] = pd.to_datetime(df["Date"])

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 Filters")

date_range = st.sidebar.date_input(
    "เลือกช่วงวันที่",
    [df["Date"].min(), df["Date"].max()]
)

machines = st.sidebar.multiselect(
    "เลือกเครื่องจักร",
    sorted(df["Machine"].dropna().unique()),
    default=sorted(df["Machine"].dropna().unique())
)

shifts = st.sidebar.multiselect(
    "เลือกกะ",
    sorted(df["Shift"].dropna().unique()),
    default=sorted(df["Shift"].dropna().unique())
)

speed_status = st.sidebar.multiselect(
    "Speed เทียบแผน",
    sorted(df["Speed_vs_Plan"].dropna().unique()),
    default=sorted(df["Speed_vs_Plan"].dropna().unique())
)

stop_types = st.sidebar.multiselect(
    "ลักษณะเวลาหยุดเครื่อง",
    sorted(df["Stop_Type"].dropna().unique()),
    default=sorted(df["Stop_Type"].dropna().unique())
)

order_lengths = st.sidebar.multiselect(
    "ลักษณะ Order ความยาว",
    sorted(df["Order_Length"].dropna().unique()),
    default=sorted(df["Order_Length"].dropna().unique())
)

# ======================================
# Apply Filters
# ======================================
filtered_df = df[
    (df["Date"] >= pd.to_datetime(date_range[0])) &
    (df["Date"] <= pd.to_datetime(date_range[1])) &
    (df["Machine"].isin(machines)) &
    (df["Shift"].isin(shifts)) &
    (df["Speed_vs_Plan"].isin(speed_status)) &
    (df["Stop_Type"].isin(stop_types)) &
    (df["Order_Length"].isin(order_lengths))
]

# ======================================
# KPI Section
# ======================================
st.title("📉 Speed & Shortage Interactive Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "จำนวน Order",
    f"{len(filtered_df):,}"
)

col2.metric(
    "Speed Actual เฉลี่ย",
    f"{filtered_df['Speed_Actual'].mean():.2f}"
)

col3.metric(
    "Speed Plan เฉลี่ย",
    f"{filtered_df['Speed_Plan'].mean():.2f}"
)

col4.metric(
    "% ต่ำกว่าแผน",
    f"{(filtered_df['Speed_Actual'] < filtered_df['Speed_Plan']).mean()*100:.1f}%"
)

st.divider()

# ======================================
# Charts
# ======================================
colA, colB = st.columns(2)

with colA:
    speed_trend = (
        filtered_df
        .groupby("Date", as_index=False)
        .agg(
            Speed_Actual=("Speed_Actual", "mean"),
            Speed_Plan=("Speed_Plan", "mean")
        )
    )

    fig_line = px.line(
        speed_trend,
        x="Date",
        y=["Speed_Actual", "Speed_Plan"],
        title="📈 Speed Actual vs Plan",
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)

with colB:
    stop_summary = (
        filtered_df
        .groupby("Stop_Type", as_index=False)
        .size()
        .rename(columns={"size": "Count"})
    )

    fig_pie = px.pie(
        stop_summary,
        names="Stop_Type",
        values="Count",
        title="🛑 สัดส่วนเวลาหยุดเครื่อง",
        hole=0.45
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ======================================
# Detail Table
# ======================================
st.subheader("📋 รายละเอียด Order")

st.dataframe(
    filtered_df.sort_values("Date", ascending=False),
    use_container_width=True,
    height=500
)
