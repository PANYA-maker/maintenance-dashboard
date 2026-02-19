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
        # โหลดข้อมูล
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

# จัดการข้อมูลประเภทตัวเลข (เฉพาะคอลัมน์คำนวณ)
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# จัดการข้อมูลประเภทข้อความ (ปรับปรุงใหม่เพื่อให้ข้อมูลไม่หาย)
text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2"]
for col in text_cols:
    if col in df.columns:
        # 1. แทนที่ค่าว่างทางสถิติ (NaN) ด้วยช่องว่างเปล่าก่อน
        df[col] = df[col].fillna("")
        # 2. แปลงเป็นข้อความ และตัดช่องว่างหน้าหลัง
        df[col] = df[col].astype(str).str.strip()
        # 3. ลบเฉพาะค่าที่เป็น "nan" หรือ "None" ที่เกิดจากการแปลงผิดพลาด (แต่ไม่ลบ "0")
        df[col] = df[col].apply(lambda x: "" if x.lower() in ['nan', 'none'] else x)

# แปลงวันที่
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
     df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

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

date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_7days, max_date])

def multi_filter(label, col):
    if col in df.columns:
        options = sorted([opt for opt in df[col].unique() if opt != ""])
        return st.sidebar.multiselect(label, options)
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
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    filtered_df = df.copy()

if machines: filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(machines)]
if shifts: filtered_df = filtered_df[filtered_df["กะ"].isin(shifts)]
if speed_status: filtered_df = filtered_df[filtered_df["Speed เทียบแผน"].isin(speed_status)]
if stop_types: filtered_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"].isin(stop_types)]
if order_lengths: filtered_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"].isin(order_lengths)]

# ======================================
# KPI CALCULATION
# ======================================
# 1. NON-STOP
non_stop_order, raw_ns_min = 0, 0.0
if "Checked-2" in filtered_df.columns:
    cond_ns = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
    non_stop_order = len(filtered_df[cond_ns])
    raw_ns_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# 2. STOP ORDERS
stop_orders_count, raw_stop_min = 0, 0.0
cond_stop = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
stop_orders_count = len(filtered_df[cond_stop])
raw_stop_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# 3. OVERALL
overall_speed_time = int(round(raw_ns_min + raw_stop_min))

# ======================================
# KPI DISPLAY
# ======================================
st.markdown("### 📊 Speed – Performance Overview")

def kpi_card(title, bg, order, minute, label_o="Order", label_m="Time Min"):
    return f"""
    <div style="background:{bg}; padding:20px 15px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">
        <h4 style="text-align:center; margin:0 0 15px 0; font-size:18px; font-weight:800; text-transform:uppercase;">{title}</h4>
        <div style="display:flex; gap:10px; justify-content:space-between;">
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                <div style="font-size:11px; opacity:0.9;">{label_o}</div>
                <div style="font-size:22px; font-weight:800;">{order:,}</div>
            </div>
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                <div style="font-size:11px; opacity:0.9;">{label_m}</div>
                <div style="font-size:22px; font-weight:800;">{minute:+,}</div>
            </div>
        </div>
    </div>
    """

c1, c2, c3 = st.columns(3)
with c1: st.markdown(kpi_card("NON-STOP", "#8e44ad", non_stop_order, int(round(raw_ns_min))), unsafe_allow_html=True)
with c2: st.markdown(kpi_card("STOP ORDERS", "#d35400", stop_orders_count, int(round(raw_stop_min))), unsafe_allow_html=True)
with c3: 
    color = "#27ae60" if overall_speed_time >= 0 else "#c0392b"
    st.markdown(kpi_card("OVERALL SPEED", color, non_stop_order + stop_orders_count, overall_speed_time), unsafe_allow_html=True)

# ======================================
# TREND CHART
# ======================================
st.markdown("---")
st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (Time Trend Analysis)")
trend_data = filtered_df.copy()
trend_data['Val'] = trend_data.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
freq_opt = st.selectbox("เลือกความถี่:", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"])

if freq_opt == "รายสัปดาห์":
    trend_data['ISO_Year'] = trend_data['วันที่'].dt.isocalendar().year
    trend_data['ISO_Week'] = trend_data['วันที่'].dt.isocalendar().week
    res = trend_data.groupby(['ISO_Year', 'ISO_Week'])['Val'].sum().reset_index()
    res['Label'] = res.apply(lambda x: f"WEEK {x['ISO_Week']}", axis=1)
else:
    m = {"รายวัน": "D", "รายเดือน": "MS", "รายปี": "YS"}
    res = trend_data.set_index('วันที่')['Val'].resample(m[freq_opt]).sum().reset_index()
    fmt = {"รายวัน": "%d/%m/%Y", "รายเดือน": "%m/%Y", "รายปี": "%Y"}
    res['Label'] = res['วันที่'].dt.strftime(fmt[freq_opt])

fig = go.Figure(go.Bar(x=res['Label'], y=res['Val'], marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res['Val']], text=res['Val'].round(0).astype(int), textposition='outside'))
fig.update_layout(height=400, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# ======================================
# TOP 10 LOSS & INSIGHTS (Fixed Columns)
# ======================================
st.markdown("---")
st.markdown("#### 🚩 10 อันดับออเดอร์ไม่จอดเครื่องที่ช้ากว่าแผนมากที่สุด")

ns_loss_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()

if not ns_loss_df.empty:
    top_10 = ns_loss_df.sort_values(by="Diff เวลา", ascending=True).head(10)
    
    # Executive Insights (ด้านบน)
    try:
        total_lost = abs(top_10["Diff เวลา"].sum())
        # กรองเอาเฉพาะที่มีข้อความจริงมาสรุป
        prob_groups = top_10[top_10["กรุ๊ปปัญหา"] != ""]["กรุ๊ปปัญหา"].value_counts()
        main_prob = prob_groups.idxmax() if not prob_groups.empty else "ไม่ระบุสาเหตุในระบบ"
        
        st.error(f"""
        **💡 Executive Insights (สรุปข้อมูล 10 อันดับที่ช้าที่สุด)**
        * **⚠️ ความสูญเสียรวม:** เฉพาะ 10 รายการนี้เสียเวลาสะสมรวม **{total_lost:,.0f} นาที** (ไม่รวมเวลาจอดเครื่อง)
        * **🏭 สาเหตุหลัก:** ปัญหาหลักเกิดจากกลุ่ม **"{main_prob}"** ซึ่งทำให้ความเร็วเฉลี่ยต่ำกว่าเป้าหมาย
        * **🔍 ข้อแนะนำ:** ควรตรวจสอบบันทึกในช่อง **"รายละเอียด"** ด้านล่างเพื่อหาวิธีป้องกันเชิงเทคนิคในกลุ่มปัญหาดังกล่าว
        """)
    except:
        st.info("ระบบกำลังประมวลผล Insights จากข้อมูลที่มีอยู่...")

    # ตารางข้อมูล
    show_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    display_df = top_10[show_cols].copy()
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        display_df[c] = display_df[c].round(0).astype(int)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ ไม่พบออเดอร์ประเภท 'ไม่จอดเครื่อง' ที่ล่าช้าในช่วงเวลานี้")

# ======================================
# Charts Row 2
# ======================================
st.divider()
c_a, c_b = st.columns(2)
with c_a:
    st.markdown("#### 📦 สัดส่วนลักษณะ Order ความยาว")
    bar_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"] != ""].groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
    fig_b = px.bar(bar_df, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_b.update_layout(height=350, template="plotly_white", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_b, use_container_width=True)

with c_b:
    st.markdown("#### 🛑 สัดส่วนลักษณะการหยุดเครื่อง")
    pie_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
    fig_p = px.pie(pie_df, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
    fig_p.update_layout(height=350, template="plotly_white", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_p, use_container_width=True)

# ======================================
# Detail Table
# ======================================
st.markdown("---")
st.subheader("📋 รายละเอียดรายการ Order (Data Logs)")
logs_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Flute", "หน้ากว้าง (W) PLAN", "ความยาวเมตร MC", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
existing = [c for c in logs_cols if c in filtered_df.columns]
st.dataframe(filtered_df[existing].sort_values("วันที่", ascending=False), use_container_width=True, height=450)
