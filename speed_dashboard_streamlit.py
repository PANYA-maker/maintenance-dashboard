import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# 1. Page Config
# ======================================
st.set_page_config(
    page_title="Speed Performance Dashboard",
    page_icon="📉",
    layout="wide"
)

# ======================================
# 2. Google Sheet Config & Loading
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

@st.cache_data(ttl=300)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("ไม่พบข้อมูล กรุณาตรวจสอบการเชื่อมต่อ Google Sheets")
    st.stop()

# ======================================
# 3. Data Cleaning (จัดการข้อความและตัวเลข)
# ======================================
df.columns = df.columns.str.strip()

# จัดการวันที่
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
    df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

# จัดการตัวเลข (ปัดเศษเบื้องต้นและจัดการค่าว่าง)
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# จัดการข้อความ (ป้องกันข้อมูลหายหลังจากปรับ Google Sheet เป็น Text)
text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2"]
for col in text_cols:
    if col in df.columns:
        # บังคับเป็น String และลบคำขยะ
        df[col] = df[col].fillna("").astype(str).str.strip()
        df[col] = df[col].apply(lambda x: "" if x.lower() in ['nan', 'none', 'null'] else x)

# ======================================
# 4. Filters (Sidebar)
# ======================================
st.sidebar.header("🔎 Filters")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

max_date = df["วันที่"].max() if df["วันที่"].notna().any() else pd.Timestamp.today()
min_date = max_date - pd.Timedelta(days=6)
date_range = st.sidebar.date_input("📅 ช่วงวันที่", [min_date, max_date])

def get_options(col):
    return sorted([opt for opt in df[col].unique() if opt != ""])

f_machines = st.sidebar.multiselect("🏭 เครื่องจักร", get_options("เครื่องจักร"))
f_shifts = st.sidebar.multiselect("⏱ กะ", get_options("กะ"))
f_stop_types = st.sidebar.multiselect("🛑 ลักษณะเวลาหยุดเครื่อง", get_options("ลักษณะ เวลาหยุดเครื่อง"))

# Apply Filtering
if len(date_range) == 2:
    mask = (df["วันที่"] >= pd.to_datetime(date_range[0])) & (df["วันที่"] <= pd.to_datetime(date_range[1]))
    f_df = df.loc[mask].copy()
else:
    f_df = df.copy()

if f_machines: f_df = f_df[f_df["เครื่องจักร"].isin(f_machines)]
if f_shifts: f_df = f_df[f_df["กะ"].isin(f_shifts)]
if f_stop_types: f_df = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"].isin(f_stop_types)]

# ======================================
# 5. KPI Calculation (Rounding to Int)
# ======================================
# Non-Stop
ns_cond = (f_df["Checked-2"].str.upper() == "YES") & (f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
ns_count = len(f_df[ns_cond])
ns_time_raw = f_df.loc[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# Stop Orders
so_cond = (f_df["Checked-2"].str.upper() == "YES") & (f_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
so_count = len(f_df[so_cond])
so_time_raw = f_df.loc[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# Overall
overall_time = int(round(ns_time_raw + so_time_raw))

# ======================================
# 6. KPI Display (UI)
# ======================================
st.markdown("### 📊 Speed – Performance Overview")

def kpi_card(title, bg, order, time, label_t="Time Min"):
    return f"""
    <div style="background:{bg}; padding:20px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom:10px;">
        <h4 style="text-align:center; margin:0 0 15px 0; font-weight:800; text-transform:uppercase; font-size:16px;">{title}</h4>
        <div style="display:flex; gap:10px; justify-content:space-between;">
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:10px; flex:1; text-align:center;">
                <div style="font-size:11px; opacity:0.8;">Order</div>
                <div style="font-size:22px; font-weight:800;">{order:,}</div>
            </div>
            <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:10px; flex:1; text-align:center;">
                <div style="font-size:11px; opacity:0.8;">{label_t}</div>
                <div style="font-size:22px; font-weight:800;">{time:+,}</div>
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
# 7. Trend Chart (ISO Week)
# ======================================
st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (Time Trend Analysis)")
trend_data = f_df.copy()
# คำนวณค่ารวมของแต่ละแถว (ช้า/เร็ว)
trend_data['Val'] = trend_data.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)

freq = st.selectbox("เลือกความถี่:", ["รายวัน", "รายสัปดาห์", "รายเดือน"])

if freq == "รายสัปดาห์":
    trend_data['ISO_Week'] = trend_data['วันที่'].dt.isocalendar().week
    res = trend_data.groupby('ISO_Week')['Val'].sum().reset_index()
    res['Label'] = res['ISO_Week'].apply(lambda x: f"WEEK {x}")
else:
    mode = {"รายวัน": "D", "รายเดือน": "MS"}
    res = trend_data.set_index('วันที่')['Val'].resample(mode[freq]).sum().reset_index()
    res['Label'] = res['วันที่'].dt.strftime("%d/%m/%Y" if freq == "รายวัน" else "%m/%Y")

fig_trend = go.Figure(go.Bar(
    x=res['Label'], y=res['Val'],
    marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res['Val']],
    text=res['Val'].round(0).astype(int), textposition='outside'
))
fig_trend.update_layout(height=400, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ======================================
# 8. Top 10 Loss & Insights
# ======================================
st.markdown("#### 🚩 10 อันดับออเดอร์ไม่จอดเครื่องที่ช้ากว่าแผนมากที่สุด")

ns_loss = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()

if not ns_loss.empty:
    # ช้ากว่าแผนคือค่าติดลบมากที่สุด (Ascending=True)
    top_10 = ns_loss.sort_values(by="Diff เวลา", ascending=True).head(10)

    # Executive Insights (ด้านบน)
    total_lost = abs(top_10["Diff เวลา"].sum())
    # หาค่าฐานนิยม (Mode) ของปัญหา
    common_probs = top_10[top_10["กรุ๊ปปัญหา"] != ""]["กรุ๊ปปัญหา"].value_counts()
    main_prob = common_probs.idxmax() if not common_probs.empty else "ไม่ระบุ"
    
    st.error(f"""
    **💡 Executive Insights (สรุปข้อมูล 10 อันดับที่ช้าที่สุด)**
    * **⚠️ วิกฤตเวลาสูญเสีย:** พบเวลาที่ล่าช้ากว่าแผนรวม **{total_lost:,.0f} นาที** จากเพียง 10 รายการนี้
    * **🏭 สาเหตุหลักที่ต้องแก้ไข:** ปัญหาส่วนใหญ่จัดอยู่ในกลุ่ม **"{main_prob}"** ซึ่งควรได้รับการตรวจสอบอย่างเร่งด่วน
    * **📉 ผลกระทบ:** ความเร็วในการผลิตจริง (Actual Speed) ต่ำกว่าเป้าหมายอย่างชัดเจนในกลุ่มรายการเหล่านี้
    * **🔍 ข้อเสนอแนะ:** ฝ่ายบริหารควรตรวจสอบช่อง "รายละเอียด" เพื่อวิเคราะห์หาสาเหตุเชิงลึก (Root Cause) ร่วมกับทีมเทคนิค
    """)

    # ตารางข้อมูล
    show_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    display_top_10 = top_10[show_cols].copy()
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        display_top_10[c] = display_top_10[c].round(0).astype(int)
    
    st.dataframe(display_top_10, use_container_width=True, hide_index=True)
else:
    st.info("ไม่พบข้อมูลออเดอร์ 'ไม่จอดเครื่อง' ในช่วงที่เลือก")

st.divider()

# ======================================
# 9. Other Charts & Logs
# ======================================
c_a, c_b = st.columns(2)
with c_a:
    st.markdown("#### 🏭 ประสิทธิภาพแยกตามเครื่องจักร")
    if "Speed เทียบแผน" in f_df.columns:
        bar_data = f_df.groupby(["เครื่องจักร", "Speed เทียบแผน"]).size().reset_index(name="C")
        fig_bar = px.bar(bar_data, x="C", y="เครื่องจักร", color="Speed เทียบแผน", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_bar.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

with c_b:
    st.markdown("#### 🛑 สัดส่วนการหยุดเครื่อง")
    pie_data = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
    fig_pie = px.pie(pie_data, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5)
    fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📋 รายละเอียดรายการ Order (Data Logs)")
logs_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
existing = [c for c in logs_cols if c in f_df.columns]
st.dataframe(f_df[existing].sort_values("วันที่", ascending=False), use_container_width=True, height=450)
