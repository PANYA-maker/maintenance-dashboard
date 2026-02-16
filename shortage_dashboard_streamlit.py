# =====================================
# Shortage Dashboard : EXECUTIVE VERSION
# MODERN UI & COMPREHENSIVE DATA
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CSS Styling (Modern Executive UI) ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* KPI Card Design */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .kpi-title {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        color: #1e293b;
        font-size: 1.875rem;
        font-weight: 700;
    }

    .kpi-sub {
        color: #94a3b8;
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }

    /* Status Badges for Insight */
    .status-critical { color: #ef4444; font-weight: 700; }
    .status-warning { color: #f59e0b; font-weight: 700; }
    .status-good { color: #10b981; font-weight: 700; }

    /* Divider Styling */
    hr {
        margin: 2rem 0 !important;
        border: 0;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Executive Shortage Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- Data Loading ----------------
SHEET_ID = "1gW0lw9XS0JYST-P-ZrXoFq0k4n2ZlXu9hOf3A--JV9U"
GID = "1799697899"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df["วันที่"] = pd.to_datetime(df["วันที่"], dayfirst=True, errors="coerce")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.warning("⚠️ ไม่พบข้อมูลในระบบ")
    st.stop()

# ---------------- Sidebar (Minimalist Style) ----------------
with st.sidebar:
    st.title("⚙️ Filter Suite")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    max_date = df["วันที่"].max()
    min_date = df["วันที่"].min()
    default_start = max_date - pd.Timedelta(days=7) if not pd.isna(max_date) else None
    
    date_range = st.date_input("🗓️ Period Selection",
        value=[default_start.date() if default_start else None, max_date.date() if not pd.isna(max_date) else None])
    
    mc_filter = st.multiselect("Machine (MC)", sorted(df["MC"].dropna().unique()))
    shift_filter = st.multiselect("Shift (กะ)", sorted(df["กะ"].dropna().unique()))
    status_filter = st.multiselect("Status (สถานะผลิต)", sorted(df["สถานะผลิต"].dropna().unique()))
    customer_filter = st.multiselect("Customer (ลูกค้า)", sorted(df["ชื่อลูกค้า"].dropna().unique()))
    period = st.selectbox("View Trend By", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"])

# ---------------- Apply Filters ----------------
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["วันที่"] >= pd.to_datetime(date_range[0])) & (fdf["วันที่"] <= pd.to_datetime(date_range[1]))]
if mc_filter: fdf = fdf[fdf["MC"].isin(mc_filter)]
if shift_filter: fdf = fdf[fdf["กะ"].isin(shift_filter)]
if status_filter: fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]
if customer_filter: fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]

# ---------------- Header ----------------
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
        <div>
            <h1 style="margin:0; color:#1e293b; font-size:2rem;">Shortage Performance Dashboard</h1>
            <p style="color:#64748b; font-size:1rem;">Production Analytics & Quality Tracking System</p>
        </div>
        <div style="text-align: right;">
            <span style="background:#f1f5f9; padding:0.5rem 1rem; border-radius:8px; color:#475569; font-weight:600; font-size:0.85rem;">
                Last Updated: {max_date.strftime('%d %b %Y') if not pd.isna(max_date) else '-'}
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================
# SECTION 1: OPERATIONAL OVERVIEW
# =========================
order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
short_pct = (short_qty / order_total * 100) if order_total > 0 else 0

st.markdown("#### 📦 Operational Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Order Total</div><div class="kpi-value">{order_total:,}</div><div class="kpi-sub">ใบงานทั้งหมด</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Completed</div><div class="kpi-value" style="color:#10b981;">{complete_qty:,}</div><div class="kpi-sub">ผลิตครบตามแผน</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Shortage</div><div class="kpi-value" style="color:#ef4444;">{short_qty:,}</div><div class="kpi-sub">ผลิตไม่ครบ (Order)</div></div>', unsafe_allow_html=True)
with c4:
    color = "#ef4444" if short_pct > 15 else "#f59e0b" if short_pct > 10 else "#10b981"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Shortage Rate</div><div class="kpi-value" style="color:{color};">{short_pct:.1f}%</div><div class="kpi-sub">เทียบใบงานทั้งหมด</div></div>', unsafe_allow_html=True)

# =========================
# SECTION 2: PHYSICAL IMPACT (METRICS)
# =========================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 📏 Physical Loss & Impact")
missing_meters = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "จำนวนเมตรขาดจำนวน"], errors="coerce").sum()
missing_sqm = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "ตารางเมตรขาดจำนวน"], errors="coerce").sum()
missing_weight = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักงานขาดจำนวน"], errors="coerce").sum()
pdw_scrap_val = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักของเหลือ PDW"], errors="coerce").sum()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Missing Meters</div><div class="kpi-value">{missing_meters:,.0f}</div><div class="kpi-sub">หน่วย: เมตร</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Missing Area</div><div class="kpi-value">{missing_sqm:,.0f}</div><div class="kpi-sub">หน่วย: ตารางเมตร</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Missing Weight</div><div class="kpi-value">{missing_weight:,.0f}</div><div class="kpi-sub">หน่วย: กิโลกรัม</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="kpi-card" style="border-left: 4px solid #f59e0b;"><div class="kpi-title">PDW Scrap Weight</div><div class="kpi-value" style="color:#b45309;">{pdw_scrap_val:,.0f}</div><div class="kpi-sub">น้ำหนักของเหลือ PDW (kg)</div></div>', unsafe_allow_html=True)

# =========================
# SECTION 3: EXECUTIVE INSIGHTS
# =========================
st.divider()
st.markdown("### 🧠 Executive Insight Summary")
if not fdf.empty and order_total > 0:
    status_class = "status-critical" if short_pct >= 20 else ("status-warning" if short_pct >= 15 else "status-good")
    status_msg = "วิกฤต (Critical)" if short_pct >= 20 else ("ต้องเฝ้าระวัง (Watchlist)" if short_pct >= 15 else "ปกติ (Healthy)")
    
    top_cause = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["Detail"].value_counts().head(1)
    main_cause_text = f"**{top_cause.index[0]}** ({top_cause.iloc[0]} Order)" if not top_cause.empty else "ยังไม่พบสาเหตุหลักชัดเจน"
    
    st.info(f"""
    🚩 **สถานะภาพรวม:** <span class="{status_class}">{status_msg}</span>  
    📉 **อัตราการขาดจำนวน:** ปัจจุบันอยู่ที่ **{short_pct:.1f}%** ของใบงานทั้งหมด  
    ⚠️ **สาเหตุวิกฤต:** สาเหตุหลักที่ทำให้งานไม่ครบคือ {main_cause_text}  
    📦 **ความสูญเสียสะสม:** ขาดรวมทั้งหมด **{missing_meters:,.0f} เมตร** และมีของเหลือ PDW สะสมถึง **{pdw_scrap_val:,.0f} กก.**
    """, icon="🚀")
else:
    st.info("กรุณาเลือกช่วงเวลาที่มีข้อมูลเพื่อรับการสรุปผลเชิงลึก")

# =========================
# SECTION 4: DEEP DIVE ANALYSIS
# =========================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 🔍 Root Cause & Distribution")
col_left, col_right = st.columns([2, 1])

with col_left:
    top10 = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail").size().sort_values().tail(10).reset_index(name="จำนวน")
    if not top10.empty:
        top10["เปอร์เซ็นต์"] = (top10["จำนวน"] / order_total * 100).round(1)
        top10["label"] = top10["จำนวน"].astype(str) + " (" + top10["เปอร์เซ็นต์"].astype(str) + "%)"
        fig_top10 = px.bar(top10, x="จำนวน", y="Detail", orientation="h", 
                          title="Top 10 Shortage Causes", 
                          color="จำนวน", color_continuous_scale="Reds", text="label")
        fig_top10.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_top10, use_container_width=True)

with col_right:
    status_df = fdf["สถานะผลิต"].value_counts().reset_index()
    status_df.columns = ["สถานะ", "จำนวน"]
    fig_status = px.pie(status_df, names="สถานะ", values="จำนวน", 
                       title="Production Status Distribution",
                       color="สถานะ", color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
    fig_status.update_traces(textinfo="percent", textfont_size=14)
    fig_status.update_layout(margin=dict(t=40, b=0, l=0, r=0), legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig_status, use_container_width=True)

# =========================
# SECTION 5: TREND ANALYSIS
# =========================
st.divider()
st.markdown("#### 📈 Production Trend Analysis")
trend = fdf.copy()
if not trend.empty:
    if period == "รายวัน": trend["ช่วง"] = trend["วันที่"].dt.strftime("%d %b")
    elif period == "รายสัปดาห์": trend["ช่วง"] = "W" + trend["วันที่"].dt.isocalendar().week.astype(str)
    elif period == "รายเดือน": trend["ช่วง"] = trend["วันที่"].dt.strftime("%b %Y")
    else: trend["ช่วง"] = trend["วันที่"].dt.year.astype(str)

    summary = trend.groupby(["ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
    summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / summary.groupby("ช่วง")["จำนวน"].transform("sum") * 100).round(1)
    
    fig_trend = px.bar(summary, x="ช่วง", y="เปอร์เซ็นต์", color="สถานะผลิต", 
                      title=f"Performance Trend ({period})",
                      text=summary["เปอร์เซ็นต์"].apply(lambda x: f'{x}%'),
                      barmode="stack", 
                      category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                      color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
    fig_trend.update_layout(yaxis_range=[0, 105], plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_trend, use_container_width=True)

# =========================
# SECTION 6: REPAIR WORKSTREAM
# =========================
st.divider()
st.markdown("### 🛠️ Repair Summary & Post-Production")
# KPI สรุปสถานะที่ย้ายมาอยู่ตรงนี้
short_order_count = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()

r_col1, r_col2 = st.columns(2)
with r_col1:
    st.markdown(f'<div class="kpi-card" style="border-top:4px solid #374151;"><div class="kpi-title">Total Shortage Orders</div><div class="kpi-value">{short_order_count:,.0f}</div><div class="kpi-sub">จำนวนใบงานที่เข้าสู่ระบบ Repair</div></div>', unsafe_allow_html=True)
with r_col2:
    st.markdown(f'<div class="kpi-card" style="border-top:4px solid #78350f;"><div class="kpi-title">Total PDW Scrap</div><div class="kpi-value">{pdw_scrap_val:,.0f}</div><div class="kpi-sub">น้ำหนักงานเสียรวม (กิโลกรัม)</div></div>', unsafe_allow_html=True)

if "สถานะซ่อมสรุป" in fdf.columns:
    issue_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].dropna(subset=["สถานะซ่อมสรุป"]).groupby("สถานะซ่อมสรุป").size().reset_index(name="จำนวน").sort_values("จำนวน", ascending=False)
    
    t1, t2 = st.columns([1, 1])
    with t1:
        st.markdown("##### 📋 Repair Category Breakdown")
        st.dataframe(issue_df, use_container_width=True, hide_index=True)
    with t2:
        fig_repair = px.pie(issue_df, names="สถานะซ่อมสรุป", values="จำนวน", hole=0.5, 
                           title="Repair Status Breakdown")
        fig_repair.update_traces(textinfo="percent+label")
        fig_repair.update_layout(margin=dict(t=30, b=0), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_repair, use_container_width=True)

# =========================
# SECTION 7: DATA EXPLORER
# =========================
st.divider()
with st.expander("📄 View Detailed Order Records"):
    fdf_display = fdf.copy()
    fdf_display["วันที่"] = fdf_display["วันที่"].dt.strftime("%d/%m/%Y")
    cols = ["วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า", "ลอน", "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป"]
    st.dataframe(fdf_display[[c for c in cols if c in fdf_display.columns]].sort_values("วันที่", ascending=False), use_container_width=True)

st.markdown("""
    <div style="text-align:center; padding: 2rem; color:#94a3b8; font-size:0.8rem;">
        Shortage Dashboard System v3.0 | Executive Intelligence Layer
    </div>
""", unsafe_allow_html=True)
