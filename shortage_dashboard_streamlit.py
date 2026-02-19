# =====================================
# Shortage Dashboard : EXECUTIVE VERSION (STABLE BUILD)
# MODERN UI & COMPREHENSIVE DATA
# UPDATED: Added Machine Performance Stacked Bar Chart
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CSS Styling (Stable Modern UI) ----------------
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    .kpi-wrapper {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .kpi-label {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-val {
        color: #1e293b;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .kpi-unit {
        color: #94a3b8;
        font-size: 0.75rem;
    }
    .section-header {
        color: #1e293b;
        font-weight: 700;
        font-size: 1.2rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #6366f1;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Shortage Intelligence Dashboard",
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

# ---------------- Sidebar Filter Suite ----------------
with st.sidebar:
    st.title("⚙️ แผงควบคุมตัวกรอง")
    if st.button("🔄 อัปเดตข้อมูลล่าสุด", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    max_date = df["วันที่"].max()
    min_date = df["วันที่"].min()
    
    if not pd.isna(max_date):
        default_start = max_date - pd.Timedelta(days=7)
    else:
        default_start = None

    date_range = st.date_input("🗓️ เลือกช่วงเวลา",
        value=[default_start.date() if default_start else None, max_date.date() if not pd.isna(max_date) else None])
    
    mc_filter = st.multiselect("Machine (MC)", sorted(df["MC"].dropna().unique()))
    shift_filter = st.multiselect("กะ (Shift)", sorted(df["กะ"].dropna().unique()))
    status_filter = st.multiselect("สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique()))
    customer_filter = st.multiselect("ชื่อลูกค้า", sorted(df["ชื่อลูกค้า"].dropna().unique()))
    period = st.selectbox("มุมมองแนวโน้ม", ["รายสัปดาห์", "รายวัน", "รายเดือน", "รายปี"])

# ---------------- Apply Filter Logic ----------------
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["วันที่"] >= pd.to_datetime(date_range[0])) & (fdf["วันที่"] <= pd.to_datetime(date_range[1]))]
if mc_filter: fdf = fdf[fdf["MC"].isin(mc_filter)]
if shift_filter: fdf = fdf[fdf["กะ"].isin(shift_filter)]
if status_filter: fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]
if customer_filter: fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]

# ---------------- Header Analytics ----------------
st.markdown(f"""
    <div style="margin-bottom: 25px;">
        <h1 style="margin:0; color:#1e293b; font-size:2.2rem;">Shortage Performance Intelligence</h1>
        <p style="color:#64748b; font-size:1.1rem;">วิเคราะห์ผลผลิตขาดจำนวน</p>
    </div>
""", unsafe_allow_html=True)

# =========================
# SECTION 1: OPERATIONAL KPIs
# =========================
order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
short_pct = (short_qty / order_total * 100) if order_total > 0 else 0

st.markdown('<div class="section-header">📦 สรุปการดำเนินงาน (Operational Summary)</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

def kpi_box(label, value, subtext, color="#1e293b"):
    st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-label">{label}</div>
            <div class="kpi-val" style="color:{color};">{value}</div>
            <div class="kpi-unit">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)

with c1: kpi_box("Order Total", f"{order_total:,}", "จำนวนใบงานทั้งหมด")
with c2: kpi_box("Completed", f"{complete_qty:,}", "ผลิตครบตามแผน", "#10b981")
with c3: kpi_box("Shortage", f"{short_qty:,}", "ผลิตไม่ครบ (Order)", "#ef4444")
with c4: 
    color_rate = "#ef4444" if short_pct > 15 else "#f59e0b" if short_pct > 10 else "#10b981"
    kpi_box("Shortage Rate", f"{short_pct:.1f}%", "สัดส่วนงานขาดจำนวน", color_rate)

# =========================
# SECTION 2: PHYSICAL LOSS IMPACT
# =========================
st.markdown('<div class="section-header">📏 ความสูญเสียเชิงกายภาพ (Physical Loss Impact)</div>', unsafe_allow_html=True)
missing_meters = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "จำนวนเมตรขาดจำนวน"], errors="coerce").sum()
missing_sqm = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "ตารางเมตรขาดจำนวน"], errors="coerce").sum()
missing_weight = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักงานขาดจำนวน"], errors="coerce").sum()
pdw_scrap_val = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักของเหลือ PDW"], errors="coerce").sum()

m1, m2, m3, m4 = st.columns(4)
with m1: kpi_box("Missing Meters", f"{missing_meters:,.0f}", "หน่วย: เมตร")
with m2: kpi_box("Missing Area", f"{missing_sqm:,.0f}", "หน่วย: ตารางเมตร")
with m3: kpi_box("Missing Weight", f"{missing_weight:,.0f}", "หน่วย: กิโลกรัม")
with m4: kpi_box("PDW Scrap Weight", f"{pdw_scrap_val:,.0f}", "ของเหลือ PDW (kg)", "#b45309")

# =========================
# SECTION 3: EXECUTIVE INSIGHTS
# =========================
st.divider()
st.subheader("🧠 สรุปสาระสำคัญสำหรับผู้บริหาร (Executive Insights)")
if not fdf.empty and order_total > 0:
    status_label = "🔴 วิกฤต (Critical)" if short_pct >= 20 else ("🟡 ต้องเฝ้าระวัง (Watchlist)" if short_pct >= 15 else "🟢 ปกติ (Healthy)")
    top_cause_series = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["Detail"].value_counts().head(1)
    main_cause = f"{top_cause_series.index[0]} ({top_cause_series.iloc[0]} Order)" if not top_cause_series.empty else "N/A"
    
    st.info(f"""
    **การวิเคราะห์ภาพรวม:**
    * **สถานะปัจจุบัน:** {status_label} ด้วยอัตราขาดจำนวน **{short_pct:.1f}%**
    * **ปัจจัยหลักที่ส่งผล:** ปัญหาหลักคือ **{main_cause}**
    * **ผลกระทบสะสม:** ขาดรวมทั้งหมด **{missing_meters:,.0f} เมตร** คิดเป็นน้ำหนักรวม **{missing_weight:,.0f} กก.**
    * **การจัดการของเสีย:** มีน้ำหนัก PDW สะสมในระบบซ่อม **{pdw_scrap_val:,.0f} กก.**
    """)
else:
    st.info("กรุณาเลือกช่วงเวลาที่มีข้อมูล")

# =========================
# SECTION 4: ROOT CAUSE & TREND
# =========================
st.markdown('<div class="section-header">🔍 วิเคราะห์สาเหตุและแนวโน้ม (Root Cause & Trend)</div>', unsafe_allow_html=True)
col_left, col_right = st.columns([2, 1])

with col_left:
    top10 = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail").size().sort_values().tail(10).reset_index(name="จำนวน")
    if not top10.empty:
        top10["%"] = (top10["จำนวน"] / order_total * 100).round(1)
        top10["label"] = top10["จำนวน"].astype(str) + " (" + top10["%"].astype(str) + "%)"
        fig_top10 = px.bar(top10, x="จำนวน", y="Detail", orientation="h", 
                          title="TOP 10 สาเหตุงานขาดจำนวน", 
                          color="จำนวน", color_continuous_scale="Reds", text="label")
        fig_top10.update_traces(textposition="auto")
        fig_top10.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, b=0))
        st.plotly_chart(fig_top10, use_container_width=True)

with col_right:
    status_df = fdf["สถานะผลิต"].value_counts().reset_index()
    status_df.columns = ["สถานะ", "จำนวน"]
    fig_status = px.pie(status_df, names="สถานะ", values="จำนวน", 
                       title="สัดส่วนสถานะการผลิต",
                       color="สถานะ", color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
    fig_status.update_traces(textinfo="percent")
    fig_status.update_layout(margin=dict(t=40, b=0), showlegend=True)
    st.plotly_chart(fig_status, use_container_width=True)

# Trend Analysis
trend = fdf.copy()
if not trend.empty:
    if period == "รายวัน": 
        trend["ช่วง_dt"] = trend["วันที่"].dt.normalize()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%d/%m/%Y")
        title_suffix = ""
    elif period == "รายสัปดาห์": 
        trend["ช่วง_dt"] = trend["วันที่"] - pd.to_timedelta((trend["วันที่"].dt.weekday + 1) % 7, unit='D')
        trend["ช่วง"] = "Week " + trend["วันที่"].dt.strftime("%U")
        title_suffix = " - เริ่มต้นสัปดาห์ที่วันอาทิตย์"
    elif period == "รายเดือน": 
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("M").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%b %Y")
        title_suffix = ""
    else: 
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("Y").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.year.astype(str)
        title_suffix = ""

    sum_trend = trend.groupby(["ช่วง_dt", "ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
    total_in_period = sum_trend.groupby("ช่วง_dt")["จำนวน"].transform("sum")
    sum_trend["%"] = (sum_trend["จำนวน"] / total_in_period * 100).round(1)
    sum_trend["label_display"] = sum_trend.apply(lambda x: f'{int(x["จำนวน"])} ({x["%"]}%)', axis=1)
    sum_trend = sum_trend.sort_values("ช่วง_dt")
    
    fig_trend = px.bar(sum_trend, x="ช่วง", y="%", color="สถานะผลิต", 
                      title=f"แนวโน้มประสิทธิภาพการผลิต ({period}{title_suffix})",
                      text="label_display",
                      barmode="stack", 
                      category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                      color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
    fig_trend.update_traces(textposition="auto")
    fig_trend.update_layout(yaxis_range=[0, 105], plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_trend, use_container_width=True)

# =========================
# SECTION 5: MACHINE PERFORMANCE (NEW SECTION)
# =========================
st.markdown('<div class="section-header">🖥️ ประสิทธิภาพรายเครื่องจักร (Machine Performance)</div>', unsafe_allow_html=True)
mc_perf = fdf.copy()
if not mc_perf.empty:
    mc_summary = mc_perf.groupby(['MC', 'สถานะผลิต']).size().reset_index(name='จำนวน')
    mc_total = mc_summary.groupby('MC')['จำนวน'].transform('sum')
    mc_summary['%'] = (mc_summary['จำนวน'] / mc_total * 100).round(1)
    mc_summary['label_display'] = mc_summary.apply(lambda x: f'{int(x["จำนวน"])} ({x["%"]}%)', axis=1)
    
    # Sort MC by name to keep it consistent
    mc_summary = mc_summary.sort_values('MC')
    
    fig_mc = px.bar(mc_summary, x="MC", y="%", color="สถานะผลิต", 
                    title="สัดส่วนสถานะการผลิตแยกตามเครื่องจักร (Compare MC Performance)",
                    text="label_display",
                    barmode="stack", 
                    category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                    color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
    
    fig_mc.update_traces(textposition="inside", textfont=dict(size=11, color="white"))
    fig_mc.update_layout(yaxis_range=[0, 105], plot_bgcolor='rgba(0,0,0,0)', 
                         xaxis_title="รหัสเครื่องจักร (MC)", yaxis_title="สัดส่วน (%)",
                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_mc, use_container_width=True)

# =========================
# SECTION 6: REPAIR & DATA EXPLORER
# =========================
st.divider()
st.markdown('<div class="section-header">🛠️ งานซ่อมและการจัดการ PDW (Repair Workstream)</div>', unsafe_allow_html=True)
short_order_count = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()

r_col1, r_col2 = st.columns(2)
with r_col1: kpi_box("Shortage Orders (Repair)", f"{short_order_count:,.0f}", "ใบงานที่ต้องดำเนินการซ่อม", "#374151")
with r_col2: kpi_box("Total PDW Scrap", f"{pdw_scrap_val:,.0f}", "น้ำหนักของเหลือรวม (กิโลกรัม)", "#78350f")

if "สถานะซ่อมสรุป" in fdf.columns:
    issue_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].dropna(subset=["สถานะซ่อมสรุป"]).groupby("สถานะซ่อมสรุป").size().reset_index(name="จำนวน").sort_values("จำนวน", ascending=False)
    
    t1, t2 = st.columns([1, 1])
    with t1:
        st.markdown("**ตารางสรุปหมวดหมู่งานซ่อม**")
        st.dataframe(issue_df, use_container_width=True, hide_index=True)
    with t2:
        fig_repair = px.pie(issue_df, names="สถานะซ่อมสรุป", values="จำนวน", hole=0.5, title="สัดส่วนปัญหาสถานะซ่อม")
        fig_repair.update_traces(textinfo="label+percent", textposition="inside", textfont_size=11, textfont_color="white")
        fig_repair.update_layout(margin=dict(t=30, b=0), showlegend=False)
        st.plotly_chart(fig_repair, use_container_width=True)

# Data Explorer
with st.expander("📄 ดูข้อมูลใบงานฉบับละเอียด (Detailed Orders)"):
    fdf_display = fdf.copy()
    fdf_display["วันที่"] = fdf_display["วันที่"].dt.strftime("%d/%m/%Y")
    cols = ["วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า", "ลอน", "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป"]
    st.dataframe(fdf_display[[c for c in cols if c in fdf_display.columns]].sort_values("วันที่", ascending=False), use_container_width=True)

st.caption("Shortage Intelligence Dashboard | Machine Performance Analysis Included | ข้อมูลครบถ้วน 100%")
