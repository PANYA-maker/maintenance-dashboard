import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("ไม่พบข้อมูล กรุณาตรวจสอบ Google Sheet")
    st.stop()

# ======================================
# Clean column names & Data
# ======================================
df.columns = df.columns.str.strip()

# ======================================
# Convert Date / Time
# ======================================
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
     df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
df["Stop Time"] = pd.to_datetime(df["Stop Time"], errors="coerce")

# แปลงตัวเลข
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ลบช่องว่างในข้อความ
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].astype(str).str.strip()

# ======================================
# Default Date
# ======================================
if df["วันที่"].notna().any():
    max_date = df["วันที่"].max()
    min_7days = max_date - pd.Timedelta(days=6)
else:
    max_date = pd.Timestamp.today()
    min_7days = max_date

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

date_range = st.sidebar.date_input(
    "📅 เลือกช่วงวันที่",
    [min_7days, max_date]
)

def multi_filter(label, col):
    if col in df.columns:
        return st.sidebar.multiselect(
            label,
            sorted(df[col].dropna().unique())
        )
    return []

machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
shifts = multi_filter("⏱ กะ", "กะ")
speed_status = multi_filter("📊 Speed เทียบแผน", "Speed เทียบแผน")
stop_types = multi_filter("🛑 ลักษณะเวลาหยุดเครื่อง", "ลักษณะ เวลาหยุดเครื่อง")
order_lengths = multi_filter("📦 ลักษณะ Order ความยาว", "ลักษณะ Order ความยาว")

# ======================================
# Apply Filters
# ======================================
if len(date_range) == 2:
    filtered_df = df[
        (df["วันที่"] >= pd.to_datetime(date_range[0])) &
        (df["วันที่"] <= pd.to_datetime(date_range[1]))
    ].copy()
else:
    filtered_df = df.copy()

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
# KPI CALCULATION
# ======================================

# 1. NON-STOP (ออเดอร์ที่ไม่จอดเครื่อง)
non_stop_order = 0
non_stop_minute = 0
if "Checked-2" in filtered_df.columns and "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
    cond_ns_count = (
        (filtered_df["Checked-2"].str.upper() == "YES") & 
        (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
    )
    non_stop_order = len(filtered_df[cond_ns_count])
    
    cond_ns_time = (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
    if "Diff เวลา" in filtered_df.columns:
        non_stop_minute = round(filtered_df.loc[cond_ns_time, "Diff เวลา"].sum())

# 2. STOP ORDERS (ออเดอร์ที่จอดเครื่อง)
stop_orders_count = 0
stop_orders_time_sum = 0
if "Checked-2" in filtered_df.columns and "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
    cond_stop_mask = (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
    cond_stop_yes = (filtered_df["Checked-2"].str.upper() == "YES") & cond_stop_mask
    stop_orders_count = len(filtered_df[cond_stop_yes])

    diff_val = filtered_df.loc[cond_stop_mask, "Diff เวลา"].sum() if "Diff เวลา" in filtered_df.columns else 0
    stop_info_val = filtered_df.loc[cond_stop_mask, "เวลาหยุดข้อมูลเครื่อง"].sum() if "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns else 0
    stop_orders_time_sum = round(diff_val + stop_info_val)

# 3. OVERALL SPEED (ภาพรวมสปีด = Non-Stop Diff Time + Stop Orders Total Time)
overall_speed_time = non_stop_minute + stop_orders_time_sum

# ======================================
# KPI DISPLAY (Compact Version)
# ======================================
st.markdown("### 📊 Speed – Performance Overview")

def kpi_card_compact(title, bg_color, order_val, minute_val, text_color="#000", order_label="Order", minute_label="Minute"):
    return f"""
    <div style="
        background:{bg_color};
        padding:15px;
        border-radius:12px;
        color:{text_color};
        box-shadow:0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    ">
        <h4 style="text-align:center; margin:0 0 10px 0; font-size:16px; font-family:sans-serif;">{title}</h4>
        <div style="display:flex; gap:8px; justify-content:space-between;">
            <div style="
                background:rgba(255,255,255,0.25);
                padding:8px;
                border-radius:8px;
                flex:1;
                text-align:center;
            ">
                <div style="font-size:11px; opacity:0.9;">{order_label}</div>
                <div style="font-size:22px; font-weight:700;">{order_val:,}</div>
            </div>
            <div style="
                background:rgba(255,255,255,0.25);
                padding:8px;
                border-radius:8px;
                flex:1;
                text-align:center;
            ">
                <div style="font-size:11px; opacity:0.9;">{minute_label}</div>
                <div style="font-size:22px; font-weight:700;">{minute_val:+,}</div>
            </div>
        </div>
    </div>
    """

# แสดง 3 คอลัมน์หลัก
col_ns, col_so, col_ov = st.columns(3)

with col_ns:
    st.markdown(kpi_card_compact("NON-STOP", "#8e44ad", non_stop_order, non_stop_minute, text_color="#fff", order_label="Order (Yes)", minute_label="Diff Time"), unsafe_allow_html=True)

with col_so:
    st.markdown(kpi_card_compact("STOP ORDERS", "#d35400", stop_orders_count, stop_orders_time_sum, text_color="#fff", order_label="Order (Yes)", minute_label="Total Time"), unsafe_allow_html=True)

with col_ov:
    overall_bg_color = "#27ae60" if overall_speed_time >= 0 else "#c0392b"
    st.markdown(kpi_card_compact(
        "OVERALL SPEED", 
        overall_bg_color, 
        non_stop_order + stop_orders_count, 
        overall_speed_time, 
        text_color="#fff", 
        order_label="Total Order", 
        minute_label="Summary Min"
    ), unsafe_allow_html=True)

st.divider()

# ======================================
# Charts Improvement
# ======================================
colA, colB = st.columns(2)

with colA:
    st.markdown("#### 📦 สัดส่วนลักษณะ Order ความยาวแยกตามเครื่องจักร")
    if "เครื่องจักร" in filtered_df.columns and "ลักษณะ Order ความยาว" in filtered_df.columns:
        bar_df = filtered_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="Order Count")
        bar_df["Percent"] = bar_df.groupby("เครื่องจักร")["Order Count"].transform(lambda x: (x / x.sum() * 100).round(1))
        
        fig_bar = px.bar(
            bar_df, 
            x="Percent", 
            y="เครื่องจักร", 
            color="ลักษณะ Order ความยาว", 
            orientation="h",
            text=bar_df.apply(lambda row: f"{row['Order Count']} ({row['Percent']}%)", axis=1),
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig_bar.update_layout(
            barmode="stack", 
            xaxis=dict(title="สัดส่วนเปอร์เซ็นต์ (%)", range=[0, 105]),
            yaxis=dict(title=None),
            height=400, 
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="closest",
            template="plotly_white"
        )
        fig_bar.update_traces(textposition='inside', insidetextanchor='middle')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลลักษณะ Order ความยาว")

with colB:
    st.markdown("#### 🛑 วิเคราะห์ลักษณะการหยุดเครื่อง (Machine Stop)")
    if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
        stop_sum = filtered_df.groupby("ลักษณะ เวลาหยุดเครื่อง", as_index=False).size().rename(columns={"size": "จำนวนครั้ง"})
        
        fig_pie = px.pie(
            stop_sum, 
            names="ลักษณะ เวลาหยุดเครื่อง", 
            values="จำนวนครั้ง", 
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        
        fig_pie.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            template="plotly_white"
        )
        fig_pie.update_traces(
            textinfo='percent+label',
            pull=[0.05] * len(stop_sum),
            marker=dict(line=dict(color='#FFFFFF', width=2))
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลลักษณะเวลาหยุดเครื่อง")

# ======================================
# Detail Table
# ======================================
st.markdown("---")
st.subheader("📋 รายละเอียดรายการ Order (Data Logs)")

full_cols_list = [
    "วันที่", "เครื่องจักร", "กะ", 
    "ลำดับที่", "PDR", "Flute", 
    "M5", "M4", "M3", "M2", "M1", 
    "หน้ากว้าง (W) PLAN", "ความยาว (L) PLAN", "T", 
    "ความยาวเมตร PLAN", "ความยาวเมตร MC", 
    "Speed Plan", "Actual Speed", "Speed เทียบแผน", 
    "เวลา Plan", "เวลา Actual", "Diff เวลา", 
    "เวลาหยุดเครื่องจากผลิต", "เวลาหยุดข้อมูลเครื่อง", 
    "Checked-1", "Checked-2", 
    "Start Time", "Stop Time", 
    "ลักษณะ Order PLAN", "ลักษณะ Order MC", 
    "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", 
    "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"
]

existing_cols = [col for col in full_cols_list if col in filtered_df.columns]

if existing_cols:
    st.dataframe(
        filtered_df[existing_cols].sort_values("วันที่", ascending=False),
        use_container_width=True,
        height=520
    )
else:
    st.warning("ไม่พบคอลัมน์ข้อมูลที่จะแสดงผล")
