# =====================================
# Shortage Dashboard : EXECUTIVE VERSION (STABLE & ROBUST)
# MODERN UI & COMPREHENSIVE DATA
# FIX: HTML Rendering issue, NameError, and Re-added Detailed Logs
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
        border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .kpi-label {
        color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
    }
    .kpi-val {
        color: #1e293b; font-size: 1.6rem; font-weight: 700; margin: 5px 0;
    }
    .kpi-unit {
        color: #94a3b8; font-size: 0.75rem;
    }
    .section-header {
        color: #1e293b; font-weight: 700; font-size: 1.2rem; margin-top: 1.5rem; margin-bottom: 1rem;
        border-left: 4px solid #6366f1; padding-left: 10px;
    }
    .analysis-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 25px;
    }
    /* Styling for Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px; border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0 0;
        gap: 1px; padding-top: 10px; color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #ef4444 !important; border-bottom: 2px solid #ef4444 !important; font-weight: 700;
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
    default_start = max_date - pd.Timedelta(days=7) if not pd.isna(max_date) else None
    date_range = st.date_input("🗓️ เลือกช่วงเวลา", value=[default_start.date() if default_start else None, max_date.date() if not pd.isna(max_date) else None])
    mc_filter = st.multiselect("Machine (MC)", sorted(df["MC"].dropna().unique()))
    shift_filter = st.multiselect("กะ (Shift)", sorted(df["กะ"].dropna().unique()))
    status_filter = st.multiselect("สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique()))
    customer_filter = st.multiselect("ชื่อลูกค้า", sorted(df["ชื่อลูกค้า"].dropna().unique()))
    stop_status_col = "สถานะ ORDER จอดหรือไม่จอด"
    stop_status_filter = st.multiselect("สถานะการจอดเครื่อง", sorted(df[stop_status_col].dropna().unique())) if stop_status_col in df.columns else []
    period = st.selectbox("มุมมองแนวโน้ม", ["รายสัปดาห์", "รายวัน", "รายเดือน", "รายปี"])

# ---------------- Apply Filter Logic ----------------
fdf = df.copy()
if len(date_range) == 2:
    fdf = fdf[(fdf["วันที่"] >= pd.to_datetime(date_range[0])) & (fdf["วันที่"] <= pd.to_datetime(date_range[1]))]
if mc_filter: fdf = fdf[fdf["MC"].isin(mc_filter)]
if shift_filter: fdf = fdf[fdf["กะ"].isin(shift_filter)]
if status_filter: fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]
if customer_filter: fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]
if stop_status_filter: fdf = fdf[fdf[stop_status_col].isin(stop_status_filter)]

# ---------------- Header Analytics ----------------
st.markdown('<div style="margin-bottom: 5px;"><h1 style="margin:0; color:#1e293b; font-size:2.2rem;">Shortage Performance Intelligence</h1></div>', unsafe_allow_html=True)
order_total = len(fdf)
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
missing_meters = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "จำนวนเมตรขาดจำนวน"], errors="coerce").sum()
missing_weight = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักงานขาดจำนวน"], errors="coerce").sum()
pdw_scrap_val = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "น้ำหนักของเหลือ PDW"], errors="coerce").sum()

# ---------------- TOP NAVIGATION TABS ----------------
tab1, tab2 = st.tabs(["📊 Executive Overview", "🛠️ Detailed Logs / Repair"])

# ==============================================================================
# TAB 1: EXECUTIVE OVERVIEW
# ==============================================================================
with tab1:
    st.markdown('<p style="color:#64748b; font-size:1.1rem; margin-bottom:20px;">วิเคราะห์ผลผลิตขาดจำนวน | ข้อมูลปัจจุบัน</p>', unsafe_allow_html=True)
    
    # Section 1: Operational Summary
    complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
    short_pct = (short_qty / order_total * 100) if order_total > 0 else 0
    st.markdown('<div class="section-header">📦 สรุปการดำเนินงาน (Operational Summary)</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    def kpi_box(label, value, subtext, color="#1e293b"):
        st.markdown(f'<div class="kpi-wrapper"><div class="kpi-label">{label}</div><div class="kpi-val" style="color:{color};">{value}</div><div class="kpi-unit">{subtext}</div></div>', unsafe_allow_html=True)
    with c1: kpi_box("Order Total", f"{order_total:,}", "จำนวนใบงานทั้งหมด")
    with c2: kpi_box("Completed", f"{complete_qty:,}", "ผลิตครบตามแผน", "#10b981")
    with c3: kpi_box("Shortage", f"{short_qty:,}", "ผลิตไม่ครบ (Order)", "#ef4444")
    with c4: kpi_box("Shortage Rate", f"{short_pct:.1f}%", "สัดส่วนงานขาดจำนวน", "#ef4444" if short_pct > 15 else "#f59e0b" if short_pct > 10 else "#10b981")

    # Section 2: Physical Loss Impact
    st.markdown('<div class="section-header">📏 ความสูญเสียเชิงกายภาพ (Physical Loss Impact)</div>', unsafe_allow_html=True)
    missing_sqm = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "ตารางเมตรขาดจำนวน"], errors="coerce").sum()
    m1, m2, m3, m4 = st.columns(4)
    with m1: kpi_box("Missing Meters", f"{missing_meters:,.0f}", "หน่วย: เมตร")
    with m2: kpi_box("Missing Area", f"{missing_sqm:,.0f}", "หน่วย: ตารางเมตร")
    with m3: kpi_box("Missing Weight", f"{missing_weight:,.0f}", "หน่วย: กิโลกรัม")
    with m4: kpi_box("PDW Scrap Weight", f"{pdw_scrap_val:,.0f}", "ของเหลือ PDW (kg)", "#b45309")

    # Section 3: Machine Comparison Analysis
    st.markdown('<div class="section-header">📊 เปรียบเทียบสัดส่วนประสิทธิภาพแยกรายเครื่องจักร (Machine Performance)</div>', unsafe_allow_html=True)
    if not fdf.empty:
        mc_group_df = fdf.groupby(['MC', 'สถานะผลิต']).size().reset_index(name='จำนวนออเดอร์')
        mc_totals = mc_group_df.groupby('MC')['จำนวนออเดอร์'].transform('sum')
        mc_group_df['เปอร์เซ็นต์สะสม'] = (mc_group_df['จำนวนออเดอร์'] / mc_totals * 100).round(1)
        mc_group_df['label_display'] = mc_group_df.apply(lambda x: f"{int(x['จำนวนออเดอร์'])} ({x['เปอร์เซ็นต์สะสม']}%)", axis=1)
        shortage_rates = mc_group_df[mc_group_df['สถานะผลิต'] == 'ขาดจำนวน'][['MC', 'เปอร์เซ็นต์สะสม']].rename(columns={'เปอร์เซ็นต์สะสม': 'short_rate'})
        mc_group_df = mc_group_df.merge(shortage_rates, on='MC', how='left').fillna({'short_rate': 0})
        mc_group_df = mc_group_df.sort_values('short_rate', ascending=True)

        fig_mc_compare = px.bar(
            mc_group_df, y="MC", x="เปอร์เซ็นต์สะสม", color="สถานะผลิต",
            title="สัดส่วนประสิทธิภาพรายเครื่องจักร (100% Normalized)",
            orientation="h", barmode="stack", text="label_display",
            color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"}
        )
        fig_mc_compare.update_traces(textposition='inside', textfont=dict(size=12, color="white", family="Arial Black"))
        fig_mc_compare.update_layout(plot_bgcolor='white', xaxis_title="เปอร์เซ็นต์ (%)", xaxis_range=[0, 100], yaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_mc_compare, use_container_width=True)

    # Section 4: Deep Dive Analysis
    st.markdown('<div class="section-header">🔍 วิเคราะห์เจาะลึกรายสาเหตุ (Deep Dive Analysis)</div>', unsafe_allow_html=True)
    col_left, col_mid, col_right = st.columns([2, 1, 1])
    with col_left:
        top10_causes = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail").size().sort_values().tail(10).reset_index(name="จำนวน")
        if not top10_causes.empty:
            top10_causes["%"] = (top10_causes["จำนวน"] / order_total * 100).round(1)
            top10_causes["label_with_pct"] = "<b>" + top10_causes["จำนวน"].map('{:,}'.format) + "</b> (" + top10_causes["%"].astype(str) + "%)"
            fig_top10 = px.bar(top10_causes, x="จำนวน", y="Detail", orientation="h", title="TOP 10 สาเหตุงานขาดจำนวน", color="จำนวน", color_continuous_scale="Reds", text="label_with_pct")
            fig_top10.update_traces(textposition="outside", textfont=dict(size=13, color="#1e293b"), cliponaxis=False)
            fig_top10.update_layout(plot_bgcolor='white', margin=dict(t=50, b=0, r=80), xaxis=dict(showgrid=True, gridcolor='lightgrey'))
            st.plotly_chart(fig_top10, use_container_width=True)
    with col_mid:
        status_counts = fdf["สถานะผลิต"].value_counts().reset_index(); status_counts.columns = ["สถานะ", "จำนวน"]
        fig_status_pie = px.pie(status_counts, names="สถานะ", values="จำนวน", title="สัดส่วนสถานะการผลิต (Overall)", color="สถานะ", color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
        fig_status_pie.update_traces(textinfo="value+percent", textfont_size=12)
        fig_status_pie.update_layout(margin=dict(t=80, b=20, l=10, r=10), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5), title=dict(y=0.9, x=0.5, xanchor='center'))
        st.plotly_chart(fig_status_pie, use_container_width=True)
    with col_right:
        short_orders = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]; stop_col_name = "สถานะ ORDER จอดหรือไม่จอด"
        if stop_col_name in short_orders.columns:
            stop_stats = short_orders[stop_col_name].value_counts().reset_index(); stop_stats.columns = ["สถานะจอด", "จำนวน"]
            fig_stop_pie = px.pie(stop_stats, names="สถานะจอด", values="จำนวน", hole=0.5, title="สัดส่วนการจอดเครื่อง (เฉพาะงานขาด)", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_stop_pie.update_traces(textinfo="value+percent", textfont_size=12)
            fig_stop_pie.update_layout(margin=dict(t=80, b=20, l=10, r=10), showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5), title=dict(y=0.9, x=0.5, xanchor='center'))
            st.plotly_chart(fig_stop_pie, use_container_width=True)

    # Section 5: Trend Analysis (Kept Chart, NameError Fixed)
    st.markdown('<div class="section-header">📈 แนวโน้มประสิทธิภาพตามช่วงเวลา</div>', unsafe_allow_html=True)
    trend_df = fdf.copy()
    trend_df = trend_df.dropna(subset=["วันที่"])
    if not trend_df.empty:
        title_suffix_str = ""
        if period == "รายวัน": 
            trend_df["ช่วง_dt"] = trend_df["วันที่"].dt.normalize()
            trend_df["ช่วง"] = trend_df["ช่วง_dt"].dt.strftime("%d/%m/%Y")
        elif period == "รายสัปดาห์":
            trend_df["ช่วง_dt"] = trend_df["วันที่"] - pd.to_timedelta((trend_df["วันที่"].dt.weekday + 1) % 7, unit='D')
            week_nums_list = trend_df["วันที่"].dt.strftime("%U").astype(int) + 1
            trend_df["ช่วง"] = "Week " + week_nums_list.apply(lambda x: f"{x:02d}")
            title_suffix_str = " - อาทิตย์"
        elif period == "รายเดือน": 
            trend_df["ช่วง_dt"] = trend_df["วันที่"].dt.to_period("M").dt.to_timestamp()
            trend_df["ช่วง"] = trend_df["ช่วง_dt"].dt.strftime("%b %Y")
        else: 
            trend_df["ช่วง_dt"] = trend_df["วันที่"].dt.to_period("Y").dt.to_timestamp()
            trend_df["ช่วง"] = trend_df["ช่วง_dt"].dt.year.astype(str)
        
        sum_trend_data = trend_df.groupby(["ช่วง_dt", "ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
        total_per_period = sum_trend_data.groupby("ช่วง_dt")["จำนวน"].transform("sum")
        sum_trend_data["%"] = (sum_trend_data["จำนวน"] / total_per_period * 100).round(1)
        sum_trend_data["label_display"] = sum_trend_data.apply(lambda x: f'{int(x["จำนวน"])} ({x["%"]}%)', axis=1)
        sum_trend_data = sum_trend_data.sort_values("ช่วง_dt")
        
        fig_trend_chart = px.bar(sum_trend_data, x="ช่วง", y="%", color="สถานะผลิต", title=f"แนวโน้มประสิทธิภาพการผลิต ({period}{title_suffix_str})", text="label_display", barmode="stack", category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]}, color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
        fig_trend_chart.update_layout(xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': sum_trend_data['ช่วง'].unique()}, yaxis_range=[0, 115], plot_bgcolor='white', legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_trend_chart, use_container_width=True)

    # Section 6: Strategic Analysis & Action Plan (Fixed HTML Rendering)
    st.markdown('<div class="section-header">💡 บทวิเคราะห์เชิงกลยุทธ์และแนวทางดำเนินงาน (Strategic Analysis & Action Plan)</div>', unsafe_allow_html=True)
    if not fdf.empty and order_total > 0:
        # Data calculations for analysis
        status_label = "🔴 วิกฤต" if short_pct > 15 else "🟡 ควรเฝ้าระวัง" if short_pct > 8 else "🟢 ปกติ"
        intensity_label = "สูง" if missing_meters > 1000 else "ปกติ"
        mc_analysis = fdf.groupby('MC')['สถานะผลิต'].apply(lambda x: (x == 'ขาดจำนวน').mean() * 100).sort_values(ascending=False)
        top_mc = mc_analysis.index[0] if not mc_analysis.empty else "N/A"
        top_mc_pct = mc_analysis.iloc[0] if not mc_analysis.empty else 0
        top_causes = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["Detail"].value_counts().head(3)
        causes_summary = ", ".join([f"{idx} ({val} ใบงาน)" for idx, val in top_causes.items()])
        
        # Use Markdown and Containers to avoid raw HTML display issues
        with st.container():
            st.markdown(f"### 🎯 บทสรุปผู้บริหาร (Executive Intelligence)")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**1. สรุปการดำเนินงาน (Operational Summary)**")
                st.write(f"- สถานะปัจจุบัน: **{status_label}**")
                st.write(f"- สัดส่วนงานขาดจำนวน: **{short_pct:.1f}%** จากทั้งหมด {order_total:,} ใบงาน")
                
                st.write(f"**2. ความสูญเสียเชิงกายภาพ (Physical Loss Impact)**")
                st.write(f"- ระดับความรุนแรง: **{intensity_label}**")
                st.write(f"- เมตรที่ขาดสะสม: **{missing_meters:,.0f} เมตร**")
                st.write(f"- ของเหลือ PDW สะสม: **{pdw_scrap_val:,.0f} กก.**")

            with col_b:
                st.write(f"**3. ประสิทธิภาพเครื่องจักร (Machine Performance)**")
                st.write(f"- เครื่องที่ต้องจับตา: **{top_mc}** (Shortage Rate: {top_mc_pct:.1f}%)")
                
                st.write(f"**4. วิเคราะห์รายสาเหตุ (Deep Dive Analysis)**")
                st.write(f"- สาเหตุหลัก 3 อันดับแรก: {causes_summary}")

            st.markdown("---")
            st.info(f"""
            **🚀 สรุปแผนปฏิบัติการแบบบูรณาการ (Integrated Action Plan)**
            1. **Prioritize MC {top_mc}:** เร่งตรวจสอบมาตรฐานการตั้งค่าเครื่องจักรและทีมงานที่ดูแลเครื่องนี้เป็นพิเศษ
            2. **Root Cause Mitigation:** มุ่งเป้าแก้ปัญหา **{top_causes.index[0] if not top_causes.empty else "N/A"}** โดยด่วนเพื่อลดปริมาณเมตรที่หายไป
            3. **PDW Management:** จัดแผนเคลียร์ PDW Scrap **{pdw_scrap_val:,.0f} กก.** ออกจากระบบเพื่อลดต้นทุนจมและเพิ่มพื้นที่จัดเก็บ
            """)
    else:
        st.info("กรุณาเลือกช่วงเวลาที่มีข้อมูลเพื่อแสดงบทวิเคราะห์")

    # Data Explorer (Returned at the bottom)
    st.markdown('<div class="section-header">📄 รายละเอียดออเดอร์ (Data Explorer)</div>', unsafe_allow_html=True)
    with st.expander("🔍 ค้นหาและดูข้อมูลใบงานฉบับละเอียด", expanded=False):
        f_c1, f_c2, f_c3 = st.columns(3)
        search_pdr_input = f_c1.text_input("ค้นหา PDR No.", placeholder="พิมพ์เลข PDR...")
        search_cust_input = f_c2.text_input("ค้นหาชื่อลูกค้า", placeholder="พิมพ์ชื่อลูกค้า...")
        search_detail_input = f_c3.text_input("ค้นหา Detail/สาเหตุ", placeholder="พิมพ์สาเหตุ...")
        
        display_df = fdf.copy()
        if search_pdr_input: display_df = display_df[display_df["PDR No."].astype(str).str.contains(search_pdr_input, case=False, na=False)]
        if search_cust_input: display_df = display_df[display_df["ชื่อลูกค้า"].astype(str).str.contains(search_cust_input, case=False, na=False)]
        if search_detail_input: display_df = display_df[display_df["Detail"].astype(str).str.contains(search_detail_input, case=False, na=False)]
        
        if not display_df.empty:
            display_df["วันที่"] = display_df["วันที่"].dt.strftime("%d/%m/%Y")
            target_cols = ["วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า", "ลอน", "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "จำนวนเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป", "สถานะ ORDER จอดหรือไม่จอด"]
            available_cols_list = [c for c in target_cols if c in display_df.columns]
            st.dataframe(display_df[available_cols_list].sort_values("ลำดับที่"), use_container_width=True, hide_index=True)
        else:
            st.info("ไม่พบข้อมูลตามเงื่อนไขที่ระบุ")

# ==============================================================================
# TAB 2: DETAILED LOGS / REPAIR
# ==============================================================================
with tab2:
    st.markdown('<div class="section-header">🛠️ งานซ่อมและการจัดการ PDW (Repair Workstream)</div>', unsafe_allow_html=True)
    repair_col = "สถานะซ่อมสรุป"
    if repair_col in fdf.columns:
        repair_data = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].dropna(subset=[repair_col]).copy()
        metrics_list = ["จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน"]
        for m_col in metrics_list:
            repair_data[m_col] = pd.to_numeric(repair_data[m_col], errors='coerce').fillna(0)
        
        repair_summary = repair_data.groupby(repair_col).agg({
            repair_col: 'size',
            'จำนวนเมตรขาดจำนวน': 'sum',
            'ตารางเมตรขาดจำนวน': 'sum',
            'น้ำหนักงานขาดจำนวน': 'sum'
        }).rename(columns={repair_col: 'จำนวนออเดอร์'}).reset_index().sort_values("จำนวนออเดอร์", ascending=False)
        
        total_o = repair_summary["จำนวนออเดอร์"].sum()
        total_m = repair_summary["จำนวนเมตรขาดจำนวน"].sum()
        total_s = repair_summary["ตารางเมตรขาดจำนวน"].sum()
        total_w = repair_summary["น้ำหนักงานขาดจำนวน"].sum()

        st.markdown(f"**สรุปสถานะงานซ่อม:** พบออเดอร์ขาดจำนวนที่ต้องจัดการทั้งหมด **{total_o:,}** ใบงาน | รวมน้ำหนักงานขาดจำนวน **{total_w:,.0f}** กก.")
        
        r_c1, r_c2 = st.columns([1.8, 1])
        with r_c1:
            st.markdown("**ตารางวิเคราะห์หมวดหมู่งานซ่อมเชิงลึก**")
            # Create a localized display dataframe
            display_repair = repair_summary.copy()
            display_repair.columns = ["หมวดหมู่งานซ่อม", "จำนวนออเดอร์", "รวมเมตร (m)", "รวม ตร.ม.", "รวมน้ำหนัก (kg)"]
            # Add total row
            total_row_df = pd.DataFrame([["ผลรวมทั้งหมด", total_o, total_m, total_s, total_w]], columns=display_repair.columns)
            display_repair = pd.concat([display_repair, total_row_df], ignore_index=True)
            st.dataframe(display_repair.style.format({"จำนวนออเดอร์": "{:,}", "รวมเมตร (m)": "{:,.0f}", "รวม ตร.ม.": "{:,.0f}", "รวมน้ำหนัก (kg)": "{:,.0f}"}), use_container_width=True, hide_index=True)
        with r_c2:
            repair_pie_data = repair_summary.copy()
            fig_repair_donut = px.pie(repair_pie_data, names=repair_col, values="จำนวนออเดอร์", hole=0.5, title="สัดส่วนออเดอร์ตามงานซ่อม")
            fig_repair_donut.update_traces(textinfo="label+percent", textposition="inside", textfont_size=11, textfont_color="white")
            fig_repair_donut.update_layout(margin=dict(t=50, b=0), showlegend=False)
            st.plotly_chart(fig_repair_donut, use_container_width=True)

st.caption("Shortage Intelligence Dashboard | Fixed HTML Display & Returned Data Explorer | ข้อมูลครบถ้วน 100%")
