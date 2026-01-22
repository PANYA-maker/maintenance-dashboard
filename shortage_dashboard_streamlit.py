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
    (
