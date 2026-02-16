# =====================================
# Shortage Dashboard : DATA CHECK
# FINAL PROD VERSION (ULTRA ANALYTICS)
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ---------------- CSS Styling ----------------
st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.25);
    color: white;
    height: 140px;
    margin-bottom: 15px;
}
.kpi-title { font-size: 14px; opacity: 0.85; }
.kpi-value { font-size: 28px; font-weight: 700; margin-top: 10px; }
.kpi-sub { font-size: 12px; opacity: 0.7; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ---------------- Page Config ----------------
st.set_page_config(page_title="Shortage Dashboard", page_icon="📊", layout="wide")

# ---------------- Google Sheet Config ----------------
SHEET_ID = "1gW0lw9XS0JYST-P-ZrXoFq0k4n2ZlXu9hOf3A--JV9U"
GID = "1799697899"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# ---------------- Load Data ----------------
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df["วันที่"] = pd.to_datetime(df["วันที่"], dayfirst=True, errors="coerce")
        # Clean numeric columns
        numeric_cols = ["จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "AVG_Speed (M/min)", "เวลาที่หยุด"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.warning("ไม่มีข้อมูลในระบบ กรุณาตรวจสอบ Google Sheet")
    st.stop()

# ---------------- Sidebar ----------------
st.sidebar.header("🔎 ตัวกรองข้อมูล")
if st.sidebar.button("🔄 โหลดข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

max_date = df["วันที่"].max()
min_date = df["วันที่"].min()
default_start = max_date - pd.Timedelta(days=7) if not pd.isna(max_date) else None

date_range = st.sidebar.date_input("เลือกช่วงวันที่", 
    value=[default_start.date() if default_start else None, max_date.date() if not pd.isna(max_date) else None])

mc_filter = st.sidebar.multiselect("MC", sorted(df["MC"].dropna().unique()))
shift_filter = st.sidebar.multiselect("กะ", sorted(df["กะ"].dropna().unique()))
status_filter = st.sidebar.multiselect("สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique()))
period = st.sidebar.selectbox("เลือกช่วงเวลา", ["รายวัน", "รายสัปดาห์", "รายเดือน"])

# ---------------- Apply Filters ----------------
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["วันที่"] >= pd.to_datetime(date_range[0])) & (fdf["วันที่"] <= pd.to_datetime(date_range[1]))]
if mc_filter: fdf = fdf[fdf["MC"].isin(mc_filter)]
if shift_filter: fdf = fdf[fdf["กะ"].isin(shift_filter)]
if status_filter: fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]

# ---------------- Header ----------------
st.markdown("""<div style="padding: 14px 18px; border-radius: 14px; background: linear-gradient(90deg, #0f172a, #020617); margin-bottom: 20px; border-left: 6px solid #ef4444;">
<h2 style="color: #f8fafc; margin: 0;">📊 SHORTAGE PERFORMANCE & DEEP ANALYSIS</h2></div>""", unsafe_allow_html=True)

# =========================
# KPI ROW 1 & 2
# =========================
order_total = len(fdf)
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
short_pct = (short_qty / order_total * 100) if order_total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">ORDER TOTAL</div><div class="kpi-value">{order_total:,}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">ขาดจำนวน (Order)</div><div class="kpi-value">{short_qty:,}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">% ขาดจำนวน</div><div class="kpi-value">{short_pct:.1f}%</div></div>', unsafe_allow_html=True)
with c4:
    avg_speed = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["AVG_Speed (M/min)"].mean()
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">AVG SPEED (งานขาด)</div><div class="kpi-value">{avg_speed:.1f}</div><div class="kpi-sub">M/min</div></div>', unsafe_allow_html=True)

k1, k2, k3 = st.columns(3)
with k1: st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #4b1212, #991b1b);"><div class="kpi-title">เมตรขาดรวม</div><div class="kpi-value">{fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["จำนวนเมตรขาดจำนวน"].sum():,.0f}</div></div>', unsafe_allow_html=True)
with k2: st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #1e3a8a, #1d4ed8);"><div class="kpi-title">ตารางเมตรขาดรวม</div><div class="kpi-value">{fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["ตารางเมตรขาดจำนวน"].sum():,.0f}</div></div>', unsafe_allow_html=True)
with k3: st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #064e3b, #047857);"><div class="kpi-title">น้ำหนักขาดรวม</div><div class="kpi-value">{fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["น้ำหนักงานขาดจำนวน"].sum():,.0f}</div></div>', unsafe_allow_html=True)

# =========================
# 🔍 NEW DEEP ANALYSIS SECTION
# =========================
st.divider()
st.subheader("🔍 วิเคราะห์เชิงลึกจากข้อมูลผลิต")
col_a, col_b = st.columns(2)

with col_a:
    # 1. ความเร็ว vs การขาดจำนวน (Box Plot)
    fig_speed = px.box(fdf, x="สถานะผลิต", y="AVG_Speed (M/min)", color="สถานะผลิต",
                       points="all", title="ความเร็วเครื่องจักรเปรียบเทียบ ครบ vs ขาด",
                       color_discrete_map={"ครบจำนวน": "#2e7d32", "ขาดจำนวน": "#c62828"})
    st.plotly_chart(fig_speed, use_container_width=True)

with col_b:
    # 2. Downtime Summary
    if "เวลาที่หยุด" in fdf.columns:
        stop_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail")["เวลาที่หยุด"].sum().reset_index().sort_values("เวลาที่หยุด", ascending=False).head(10)
        fig_stop = px.bar(stop_df, x="เวลาที่หยุด", y="Detail", orientation="h",
                          title="10 สาเหตุที่เสียเวลาหยุดผลิตนานที่สุด (งานขาดจำนวน)",
                          color="เวลาที่หยุด", color_continuous_scale="Reds")
        st.plotly_chart(fig_stop, use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    # 3. MC x Shift Heatmap
    heat_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby(["MC", "กะ"]).size().reset_index(name="จำนวนครั้ง")
    fig_heat = px.density_heatmap(heat_df, x="กะ", y="MC", z="จำนวนครั้ง", text_auto=True,
                                  title="จุดวิกฤต: เครื่องจักรไหน กะไหน ขาดบ่อยที่สุด?",
                                  color_continuous_scale="OrRd")
    st.plotly_chart(fig_heat, use_container_width=True)

with col_d:
    # 4. ลอน (Profile) Analysis
    if "ลอน" in fdf.columns:
        lon_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("ลอน").size().reset_index(name="Order")
        fig_lon = px.pie(lon_df, names="ลอน", values="Order", hole=0.4, title="สัดส่วนปัญหาแยกตามหน้าลอน (Profile)")
        fig_lon.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_lon, use_container_width=True)

# ---------------- TREND ----------------
st.divider()
st.subheader("📈 แนวโน้มสถานะผลิตตามช่วงเวลา")
trend = fdf.copy()
if period == "รายวัน": trend["ช่วง"] = trend["วันที่"].dt.strftime("%d/%m/%Y")
elif period == "รายสัปดาห์": trend["ช่วง"] = trend["วันที่"].dt.isocalendar().week.astype(str)
else: trend["ช่วง"] = trend["วันที่"].dt.strftime("%b %Y")

summary = trend.groupby(["ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
total = summary.groupby("ช่วง")["จำนวน"].transform("sum")
summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / total * 100).round(1)

fig_trend = px.bar(summary, x="ช่วง", y="เปอร์เซ็นต์", color="สถานะผลิต", barmode="stack", text=summary["เปอร์เซ็นต์"].apply(lambda x: f'{x}%'),
                   category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                   color_discrete_map={"ครบจำนวน": "#2e7d32", "ขาดจำนวน": "#c62828", "ยกเลิกผลิต": "#ff4b4b"})
st.plotly_chart(fig_trend, use_container_width=True)

# ---------------- DATA TABLE ----------------
st.divider()
st.subheader("📋 รายละเอียด Order")
st.dataframe(fdf.sort_values("วันที่", ascending=False), use_container_width=True)
st.caption("Shortage Dashboard | FINAL PROD | Advanced Analysis")
