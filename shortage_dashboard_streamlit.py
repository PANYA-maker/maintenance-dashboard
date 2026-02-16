# =====================================
# Shortage Dashboard : DATA CHECK
# FINAL PROD VERSION (FIXED INSIGHT TEXT)
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px

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

.kpi-title {
    font-size: 14px;
    opacity: 0.85;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    margin-top: 10px;
}

.kpi-sub {
    font-size: 12px;
    opacity: 0.7;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

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

# ---------------- Load Data (Auto Refresh) ----------------
@st.cache_data(ttl=300)  # 🔄 refresh ทุก 5 นาที
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()

        df["วันที่"] = pd.to_datetime(
            df["วันที่"],
            dayfirst=True,
            errors="coerce"
        )
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

if st.sidebar.button("🔄 โหลดข้อมูลล่าสุดจาก Google Sheet"):
    st.cache_data.clear()
    st.rerun()

# Date Range Logic
max_date = df["วันที่"].max()
min_date = df["วันที่"].min()
default_start = max_date - pd.Timedelta(days=7) if not pd.isna(max_date) else None

date_range = st.sidebar.date_input(
    "เลือกช่วงวันที่",
    value=[default_start.date() if default_start else None, max_date.date() if not pd.isna(max_date) else None],
    min_value=min_date.date() if not pd.isna(min_date) else None,
    max_value=max_date.date() if not pd.isna(max_date) else None
)

mc_filter = st.sidebar.multiselect("MC", sorted(df["MC"].dropna().unique()))
shift_filter = st.sidebar.multiselect("กะ", sorted(df["กะ"].dropna().unique()))
status_filter = st.sidebar.multiselect("สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique()))
customer_filter = st.sidebar.multiselect("ชื่อลูกค้า", sorted(df["ชื่อลูกค้า"].dropna().unique()))

st.sidebar.subheader("📊 แนวโน้มตามช่วงเวลา")
period = st.sidebar.selectbox("เลือกช่วงเวลา", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"])

# ---------------- Apply Filters ----------------
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["วันที่"] >= pd.to_datetime(date_range[0])) & (fdf["วันที่"] <= pd.to_datetime(date_range[1]))]

if mc_filter: fdf = fdf[fdf["MC"].isin(mc_filter)]
if shift_filter: fdf = fdf[fdf["กะ"].isin(shift_filter)]
if status_filter: fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]
if customer_filter: fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]

# ---------------- Main Header ----------------
st.markdown(
    """
    <div style="padding: 14px 18px; border-radius: 14px; background: linear-gradient(90deg, #0f172a, #020617); margin: 12px 0 20px 0; border-left: 6px solid #ef4444;">
        <h2 style="color: #f8fafc; margin: 0; font-weight: 700; letter-spacing: 1px;">📊 SHORTAGE PERFORMANCE</h2>
        <p style="margin: 6px 0 0 0; color: #cbd5f5; font-size: 14px;">ภาพรวมผลการผลิต (Order / ครบจำนวน / ขาดจำนวน / % ขาดจำนวน)</p>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# KPI ROW 1 : ORDER & STATUS
# =========================
order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
short_pct = (short_qty / order_total * 100) if order_total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">ORDER TOTAL</div><div class="kpi-value">{order_total:,}</div><div class="kpi-sub">จำนวนใบงานทั้งหมด</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">ครบจำนวน</div><div class="kpi-value">{complete_qty:,}</div><div class="kpi-sub">ใบงานที่ผลิตครบ</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">ขาดจำนวน</div><div class="kpi-value">{short_qty:,}</div><div class="kpi-sub">ใบงานที่ผลิตไม่ครบ (Order)</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">% ขาดจำนวน</div><div class="kpi-value">{short_pct:.1f}%</div><div class="kpi-sub">เทียบใบงานทั้งหมด</div></div>', unsafe_allow_html=True)

# =========================
# KPI ROW 2 : SHORTAGE METRICS (METERS / SQM / WEIGHT)
# =========================
missing_meters = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "จำนวนเมตรขาดจำนวน"], errors="coerce").sum()
missing_sqm = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "ตารางเมตรขาดจำนวน"], errors="coerce").sum()
missing_weight = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักงานขาดจำนวน"], errors="coerce").sum()

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #4b1212, #7f1d1d, #991b1b);"><div class="kpi-title">ผลรวมจำนวนเมตรขาดจำนวน</div><div class="kpi-value">{missing_meters:,.0f}</div><div class="kpi-sub">หน่วย: เมตร</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #1e3a8a, #1e40af, #1d4ed8);"><div class="kpi-title">ผลรวมตารางเมตรขาดจำนวน</div><div class="kpi-value">{missing_sqm:,.0f}</div><div class="kpi-sub">หน่วย: ตารางเมตร</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card" style="background: linear-gradient(135deg, #064e3b, #065f46, #047857);"><div class="kpi-title">ผลรวมน้ำหนักงานขาดจำนวน</div><div class="kpi-value">{missing_weight:,.0f}</div><div class="kpi-sub">หน่วย: กิโลกรัม</div></div>', unsafe_allow_html=True)

st.divider()

# =========================
# ⏰ AUTO INSIGHT (Executive Summary)
# =========================
st.markdown("### 🧠 Executive Insight")
if not fdf.empty and order_total > 0:
    status_msg = "🔴 อยู่ในระดับวิกฤต" if short_pct >= 20 else ("🟡 ต้องเฝ้าระวัง" if short_pct >= 15 else "🟢 อยู่ในเกณฑ์ควบคุมได้")
    top_cause = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["Detail"].value_counts().head(1)
    main_cause_text = f"สาเหตุหลักคือ **{top_cause.index[0]}** ({top_cause.iloc[0]} Order)" if not top_cause.empty else "ยังไม่พบสาเหตุหลักชัดเจน"
    
    pdw_col = "น้ำหนักของเหลือ PDW"
    pdw_text = ""
    if pdw_col in fdf.columns:
        pdw_sum = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", pdw_col], errors="coerce").fillna(0).sum()
        pdw_text = f" | น้ำหนักของเหลือ PDW รวม: **{pdw_sum:,.0f} KG**"

    st.info(f"""
    📊 **ภาพรวมช่วงเวลาที่เลือก**
    - ORDER TOTAL : **{order_total:,}**
    - ขาดจำนวน : **{short_qty:,} Order** (**{short_pct:.1f}%**) → {status_msg}  
    - {main_cause_text}  
    - เมตรขาดรวม: **{missing_meters:,.0f} ม.** | ตร.ม. ขาดรวม: **{missing_sqm:,.0f} ตร.ม.** {pdw_text}
    """)
else:
    st.info("ไม่มีข้อมูลเพียงพอสำหรับสรุปผล")

# ---------------- TOP 10 + Donut ----------------
left, right = st.columns([2, 1])

with left:
    top10 = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail").size().sort_values().tail(10).reset_index(name="จำนวน")
    if not top10.empty:
        top10["เปอร์เซ็นต์"] = (top10["จำนวน"] / order_total * 100).round(1)
        top10["label"] = top10["จำนวน"].astype(str) + " (" + top10["เปอร์เซ็นต์"].astype(str) + "%)"
        fig_top10 = px.bar(top10, x="จำนวน", y="Detail", orientation="h", title="TOP 10 สาเหตุขาดจำนวน", color="จำนวน", color_continuous_scale="Reds", text="label")
        
        fig_top10.update_traces(
            textposition="inside", 
            insidetextanchor="end", 
            textfont=dict(color="white", size=12, family="Arial") 
        )
        fig_top10.update_layout(
            title_font_size=16,
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12)),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_top10, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลขาดจำนวนในช่วงที่เลือก")

with right:
    status_df = fdf["สถานะผลิต"].value_counts().reset_index()
    status_df.columns = ["สถานะ", "จำนวน"]
    fig_status = px.pie(
        status_df, 
        names="สถานะ", 
        values="จำนวน", 
        hole=0, 
        title="สัดส่วนสถานะผลิต", 
        color="สถานะ", 
        color_discrete_map={
            "ครบจำนวน": "#2e7d32", 
            "ขาดจำนวน": "#c62828",
            "ยกเลิกผลิต": "#ff4b4b"
        }
    )
    
    fig_status.update_traces(
        textinfo="percent", 
        textposition="inside",
        textfont=dict(size=14, color="white", family="Arial Black"), 
        insidetextorientation='horizontal'
    )
    fig_status.update_layout(
        title_font_size=16, 
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_status, use_container_width=True)

# ---------------- STACKED BAR TREND ----------------
st.divider()
st.subheader("📊 เปอร์เซ็นต์ ครบจำนวน / ขาดจำนวน (แนวโน้มตามช่วงเวลา)")
trend = fdf.copy()
if not trend.empty:
    if period == "รายวัน":
        trend["ช่วง_dt"] = trend["วันที่"].dt.normalize()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%d/%m/%Y")
    elif period == "รายสัปดาห์":
        trend["ช่วง_dt"] = trend["วันที่"] - pd.to_timedelta((trend["วันที่"].dt.weekday + 1) % 7, unit="D")
        trend["ช่วง"] = "Week " + (((trend["ช่วง_dt"] - (pd.to_datetime(trend["ช่วง_dt"].dt.year.astype(str) + "-01-01") - pd.to_timedelta((pd.to_datetime(trend["ช่วง_dt"].dt.year.astype(str) + "-01-01").dt.weekday + 1) % 7, unit="D"))).dt.days // 7) + 1).astype(str) + " / " + trend["ช่วง_dt"].dt.year.astype(str)
    elif period == "รายเดือน":
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("M").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%b %Y")
    else: # รายปี
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("Y").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.year.astype(str)

    summary = trend.groupby(["ช่วง_dt", "ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
    total = summary.groupby(["ช่วง_dt", "ช่วง"])["จำนวน"].sum().reset_index(name="รวม")
    summary = summary.merge(total, on=["ช่วง_dt", "ช่วง"])
    summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / summary["รวม"] * 100).round(1)
    summary["label"] = summary["จำนวน"].astype(str) + " (" + summary["เปอร์เซ็นต์"].astype(str) + "%)"
    summary = summary.sort_values("ช่วง_dt")
    
    fig_stack = px.bar(
        summary, 
        x="ช่วง", 
        y="เปอร์เซ็นต์", 
        color="สถานะผลิต", 
        text="label", 
        barmode="stack", 
        category_orders={
            "สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]
        },
        color_discrete_map={
            "ครบจำนวน": "#2e7d32", 
            "ขาดจำนวน": "#c62828",
            "ยกเลิกผลิต": "#ff4b4b"
        }
    )
    
    fig_stack.update_layout(
        yaxis_range=[0, 100], 
        yaxis_title="เปอร์เซ็นต์ (%)", 
        xaxis_title="ช่วงเวลา",
        title_font_size=16,
        xaxis=dict(tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=12))
    )
    fig_stack.update_traces(textfont=dict(size=11))
    
    st.plotly_chart(fig_stack, use_container_width=True)

# ---------------- REPAIR SUMMARY ----------------
st.divider()
st.subheader("🛠️ สรุปปัญหาสถานะซ่อม (เฉพาะงานขาดจำนวน)")

# =========================
# KPI ROW (UNDER REPAIR HEADER)
# =========================
# ย้ายตำแหน่งการคำนวณและการแสดงผล KPI มาไว้ใต้ Header ทันที
short_order_count = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
pdw_scrap_val = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักของเหลือ PDW"], errors="coerce").sum()

col_kpi_a, col_kpi_b = st.columns(2)
with col_kpi_a:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #374151, #1f2937, #111827);">
        <div class="kpi-title">ผลรวมขาดจำนวน</div>
        <div class="kpi-value">{short_order_count:,.0f}</div>
        <div class="kpi-sub">หน่วย: ORDER</div>
    </div>
    """, unsafe_allow_html=True)

with col_kpi_b:
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #78350f, #92400e, #b45309);">
        <div class="kpi-title">น้ำหนักของเหลือ PDW</div>
        <div class="kpi-value">{pdw_scrap_val:,.0f}</div>
        <div class="kpi-sub">หน่วย: กิโลกรัม</div>
    </div>
    """, unsafe_allow_html=True)

if "สถานะซ่อมสรุป" in fdf.columns:
    issue_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].dropna(subset=["สถานะซ่อมสรุป"]).groupby("สถานะซ่อมสรุป").size().reset_index(name="จำนวน").sort_values("จำนวน", ascending=False)
    
    if not issue_df.empty:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### 📋 ตารางสรุปปัญหา")
            st.dataframe(issue_df, use_container_width=True, height=350)
        with c2:
            fig_issue = px.pie(
                issue_df, 
                names="สถานะซ่อมสรุป", 
                values="จำนวน", 
                hole=0.5, 
                title="สัดส่วนปัญหาสถานะซ่อม"
            )
            fig_issue.update_traces(
                textinfo="percent+label", 
                textposition="inside",
                textfont=dict(size=12, color="white", family="Arial Black")
            )
            fig_issue.update_layout(title_font_size=16)
            st.plotly_chart(fig_issue, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถานะซ่อมสำหรับงานขาดจำนวน")
else:
    st.warning("ไม่พบคอลัมน์ 'สถานะซ่อมสรุป'")

# ---------------- DATA TABLE ----------------
st.divider()
st.subheader("📋 รายละเอียด Order")
fdf_display = fdf.copy()
fdf_display["วันที่"] = fdf_display["วันที่"].dt.strftime("%d/%m/%Y")

display_columns = [
    "วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า", "ลอน", 
    "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "จำนวนเมตรขาดจำนวน", 
    "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป"
]
display_columns = [c for c in display_columns if c in fdf_display.columns]

st.dataframe(
    fdf_display[display_columns].sort_values("วันที่", ascending=False),
    use_container_width=True,
    height=500
)

st.caption("Shortage Dashboard | FINAL PROD VERSION | High Visibility Build")
