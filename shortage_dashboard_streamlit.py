# =====================================
# Shortage Dashboard : EXECUTIVE VERSION (TOP NAVIGATION)
# MODERN UI & COMPREHENSIVE DATA
# UPDATED: Fixed Top 10 Causes Chart to match original visual style
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
    /* Styling for Tabs to look more like the reference image */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #ef4444 !important;
        border-bottom: 2px solid #ef4444 !important;
        font-weight: 700;
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
    
    stop_status_col = "สถานะ ORDER จอดหรือไม่จอด"
    if stop_status_col in df.columns:
        stop_status_filter = st.multiselect("สถานะการจอดเครื่อง", sorted(df[stop_status_col].dropna().unique()))
    else:
        stop_status_filter = []

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
st.markdown(f"""
    <div style="margin-bottom: 5px;">
        <h1 style="margin:0; color:#1e293b; font-size:2.2rem;">Shortage Performance Intelligence</h1>
    </div>
""", unsafe_allow_html=True)

# Shared Calculations
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
    st.markdown('<p style="color:#64748b; font-size:1.1rem; margin-bottom:20px;">วิเคราะห์ผลผลิตขาดจำนวน | เริ่มต้น 7 วันล่าสุด (Week Cycle: อาทิตย์ - เสาร์)</p>', unsafe_allow_html=True)
    
    # Section 1: Operational Summary
    complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
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

    # Section 2: Physical Loss Impact
    st.markdown('<div class="section-header">📏 ความสูญเสียเชิงกายภาพ (Physical Loss Impact)</div>', unsafe_allow_html=True)
    missing_sqm = pd.to_numeric(fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", "ตารางเมตรขาดจำนวน"], errors="coerce").sum()
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: kpi_box("Missing Meters", f"{missing_meters:,.0f}", "หน่วย: เมตร")
    with m2: kpi_box("Missing Area", f"{missing_sqm:,.0f}", "หน่วย: ตารางเมตร")
    with m3: kpi_box("Missing Weight", f"{missing_weight:,.0f}", "หน่วย: กิโลกรัม")
    with m4: kpi_box("PDW Scrap Weight", f"{pdw_scrap_val:,.0f}", "ของเหลือ PDW (kg)", "#b45309")

    # Section 3: Machine Performance Analysis
    st.markdown('<div class="section-header">🖥️ ประสิทธิภาพรายเครื่องจักร (Machine Performance Analysis)</div>', unsafe_allow_html=True)
    mc_perf = fdf.copy()
    if not mc_perf.empty:
        mc_summary = mc_perf.groupby(['MC', 'สถานะผลิต']).size().reset_index(name='จำนวน')
        mc_total = mc_summary.groupby('MC')['จำนวน'].transform('sum')
        mc_summary['%'] = (mc_summary['จำนวน'] / mc_total * 100).round(1)
        mc_summary['label_display'] = mc_summary.apply(lambda x: f'{int(x["จำนวน"])} ({x["%"]}%)', axis=1)
        sort_helper = mc_summary[mc_summary['สถานะผลิต'] == 'ขาดจำนวน'][['MC', '%']].rename(columns={'%': 'sort_pct'})
        mc_summary = mc_summary.merge(sort_helper, on='MC', how='left').fillna({'sort_pct': 0})
        mc_summary = mc_summary.sort_values(['sort_pct', 'MC'], ascending=[True, True])
        
        fig_mc = px.bar(mc_summary, x="%", y="MC", color="สถานะผลิต", orientation="h",
                        title="เปรียบเทียบสัดส่วนประสิทธิภาพแยกตามเครื่องจักร",
                        text="label_display", barmode="stack", 
                        category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                        color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
        fig_mc.update_traces(textposition="inside", textfont=dict(size=12, color="white", family="Arial Black"), marker_line_width=0)
        fig_mc.update_layout(xaxis_range=[0, 105], plot_bgcolor='rgba(0,0,0,0)', xaxis_title="เปอร์เซ็นต์สะสม (%)", 
                             yaxis_title=None, height=min(400 + (len(mc_summary['MC'].unique()) * 30), 800),
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_mc, use_container_width=True)

    # Section 4: Deep Dive & Trend
    st.markdown('<div class="section-header">🔍 วิเคราะห์สาเหตุและเจาะลึกงานขาดจำนวน (Deep Dive Analysis)</div>', unsafe_allow_html=True)
    col_left, col_mid, col_right = st.columns([2, 1, 1])
    
    with col_left:
        # FIXED: Top 10 Causes Chart (Matching image_be3377.png)
        top10 = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].groupby("Detail").size().sort_values().tail(10).reset_index(name="จำนวน")
        if not top10.empty:
            fig_top10 = px.bar(top10, x="จำนวน", y="Detail", orientation="h", 
                              title="TOP 10 สาเหตุงานขาดจำนวน", 
                              color="จำนวน", 
                              color_continuous_scale="Reds", 
                              text="จำนวน")
            fig_top10.update_traces(textposition="inside", textfont=dict(size=12, color="white"))
            fig_top10.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white',
                margin=dict(t=50, b=0),
                coloraxis_colorbar=dict(title="จำนวน"),
                xaxis=dict(showgrid=True, gridcolor='lightgrey'),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_top10, use_container_width=True)

    with col_mid:
        status_df = fdf["สถานะผลิต"].value_counts().reset_index(); status_df.columns = ["สถานะ", "จำนวน"]
        fig_status = px.pie(status_df, names="สถานะ", values="จำนวน", title="สัดส่วนสถานะผลิต (Overall)",
                           color="สถานะ", color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
        fig_status.update_traces(textinfo="value+percent", textfont_size=11); fig_status.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_status, use_container_width=True)
        
    with col_right:
        short_df = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]; stop_col = "สถานะ ORDER จอดหรือไม่จอด"
        if stop_col in short_df.columns:
            stop_summary = short_df[stop_col].value_counts().reset_index(); stop_summary.columns = ["สถานะจอด", "จำนวน"]
            fig_stop = px.pie(stop_summary, names="สถานะจอด", values="จำนวน", title="สัดส่วนการจอดเครื่อง (เฉพาะงานขาด)", color_discrete_sequence=px.colors.qualitative.Safe)
            fig_stop.update_traces(textinfo="value+percent", textfont_size=11); fig_stop.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_stop, use_container_width=True)

    st.markdown("#### 📈 แนวโน้มประสิทธิภาพตามช่วงเวลา")
    trend = fdf.copy()
    if not trend.empty:
        if period == "รายวัน": 
            trend["ช่วง_dt"] = trend["วันที่"].dt.normalize(); trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%d/%m/%Y")
        elif period == "รายสัปดาห์": 
            trend["ช่วง_dt"] = trend["วันที่"] - pd.to_timedelta((trend["วันที่"].dt.weekday + 1) % 7, unit='D')
            # Updated week logic for Sunday start with offset +1
            week_nums = trend["วันที่"].dt.strftime("%U").astype(int) + 1; trend["ช่วง"] = "Week " + week_nums.apply(lambda x: f"{x:02d}")
        elif period == "รายเดือน": 
            trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("M").dt.to_timestamp(); trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%b %Y")
        else: 
            trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("Y").dt.to_timestamp(); trend["ช่วง"] = trend["ช่วง_dt"].dt.year.astype(str)

        sum_trend = trend.groupby(["ช่วง_dt", "ช่วง", "สถานะผลิต"]).size().reset_index(name="จำนวน")
        total_in_period = sum_trend.groupby("ช่วง_dt")["จำนวน"].transform("sum")
        sum_trend["%"] = (sum_trend["จำนวน"] / total_in_period * 100).round(1); sum_trend["label_display"] = sum_trend.apply(lambda x: f'{int(x["จำนวน"])} ({x["%"]}%)', axis=1)
        sum_trend = sum_trend.sort_values("ช่วง_dt")
        
        cust_display = f" | ลูกค้า: {', '.join(customer_filter)}" if customer_filter and len(customer_filter) <= 3 else (f" | ลูกค้า {len(customer_filter)} ราย" if customer_filter else "")
        fig_trend = px.bar(sum_trend, x="ช่วง", y="%", color="สถานะผลิต", title=f"แนวโน้มประสิทธิภาพการผลิต ({period}){cust_display}",
                          text="label_display", barmode="stack", category_orders={"สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน", "ยกเลิกผลิต"]},
                          color_discrete_map={"ครบจำนวน": "#10b981", "ขาดจำนวน": "#ef4444", "ยกเลิกผลิต": "#94a3b8"})
        fig_trend.update_layout(xaxis={'type': 'category', 'categoryorder': 'array', 'categoryarray': sum_trend['ช่วง'].unique()},
                                yaxis_range=[0, 115], plot_bgcolor='white', legend=dict(orientation="h", y=-0.2), margin=dict(t=50))
        fig_trend.update_traces(textposition="inside", textfont=dict(size=10, color="white"), insidetextanchor="middle")
        st.plotly_chart(fig_trend, use_container_width=True)

# ==============================================================================
# TAB 2: DETAILED LOGS / REPAIR
# ==============================================================================
with tab2:
    st.markdown('<div class="section-header">🛠️ งานซ่อมและการจัดการ PDW (Repair Workstream)</div>', unsafe_allow_html=True)
    
    if "สถานะซ่อมสรุป" in fdf.columns:
        # Data Preparation
        repair_summary_data = fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"].dropna(subset=["สถานะซ่อมสรุป"]).copy()
        metrics = ["จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน"]
        for m in metrics:
            repair_summary_data[m] = pd.to_numeric(repair_summary_data[m], errors='coerce').fillna(0)
        
        # Grouping
        issue_df = repair_summary_data.groupby("สถานะซ่อมสรุป").agg({
            'สถานะซ่อมสรุป': 'size',
            'จำนวนเมตรขาดจำนวน': 'sum',
            'ตารางเมตรขาดจำนวน': 'sum',
            'น้ำหนักงานขาดจำนวน': 'sum'
        }).rename(columns={'สถานะซ่อมสรุป': 'จำนวนออเดอร์'}).reset_index().sort_values("จำนวนออเดอร์", ascending=False)
        
        total_orders = issue_df["จำนวนออเดอร์"].sum()
        total_meters = issue_df["จำนวนเมตรขาดจำนวน"].sum()
        total_sqm = issue_df["ตารางเมตรขาดจำนวน"].sum()
        total_weight = issue_df["น้ำหนักงานขาดจำนวน"].sum()

        # Build Total Row
        total_row = pd.DataFrame([{
            "สถานะซ่อมสรุป": "ผลรวมทั้งหมด",
            "จำนวนออเดอร์": total_orders,
            "จำนวนเมตรขาดจำนวน": total_meters,
            "ตารางเมตรขาดจำนวน": total_sqm,
            "น้ำหนักงานขาดจำนวน": total_weight
        }])
        issue_df = pd.concat([issue_df, total_row], ignore_index=True)
        issue_df.columns = ["หมวดหมู่งานซ่อม", "จำนวนออเดอร์", "รวมเมตร (m)", "รวม ตร.ม.", "รวมน้ำหนัก (kg)"]

        # RESTORED SUMMARY BOX (Matching image_be9899.png)
        st.markdown(f"""
        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
            <p style="margin:0; font-size: 1.1rem; color: #334155;">
                <b>สรุปสถานะงานซ่อม:</b> พบออเดอร์ขาดจำนวนที่ต้องจัดการทั้งหมด <b>{total_orders:,}</b> ใบงาน | 
                รวมน้ำหนักงานขาดจำนวน <b>{total_weight:,.0f}</b> กก. | 
                น้ำหนักของเหลือ PDW สะสม <b>{pdw_scrap_val:,.0f}</b> กก.
            </p>
        </div>
        """, unsafe_allow_html=True)

        t1, t2 = st.columns([1.8, 1])
        with t1:
            st.markdown("**ตารางวิเคราะห์หมวดหมู่งานซ่อมเชิงลึก**")
            st.dataframe(
                issue_df.style.format({
                    "จำนวนออเดอร์": "{:,}",
                    "รวมเมตร (m)": "{:,.0f}",
                    "รวม ตร.ม.": "{:,.0f}",
                    "รวมน้ำหนัก (kg)": "{:,.0f}"
                }),
                use_container_width=True, hide_index=True
            )
        with t2:
            issue_df_pie = issue_df[issue_df["หมวดหมู่งานซ่อม"] != "ผลรวมทั้งหมด"]
            fig_repair = px.pie(issue_df_pie, names="หมวดหมู่งานซ่อม", values="จำนวนออเดอร์", hole=0.5, title="สัดส่วนออเดอร์ตามงานซ่อม")
            fig_repair.update_traces(textinfo="label+percent", textposition="inside", textfont_size=11, textfont_color="white")
            fig_repair.update_layout(margin=dict(t=30, b=0), showlegend=False)
            st.plotly_chart(fig_repair, use_container_width=True)

    # Data Explorer Expander (Moved to Tab 2 to keep Overview clean)
    with st.expander("📄 ดูข้อมูลใบงานฉบับละเอียด (Detailed Orders)"):
        st.markdown("🔍 **กรองข้อมูลเฉพาะในตาราง**")
        f_c1, f_c2, f_c3 = st.columns(3)
        target_columns = ["วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า", "ลอน", "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "จำนวนเมตรขาดจำนวน", "ตารางเมตรขาดจำนวน", "น้ำหนักงานขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป", "สถานะ ORDER จอดหรือไม่จอด"]
        search_pdr = f_c1.text_input("ค้นหา PDR No.", placeholder="พิมพ์เลข PDR..."); search_cust = f_c2.text_input("ค้นหาชื่อลูกค้า", placeholder="พิมพ์ชื่อลูกค้า..."); search_detail = f_c3.text_input("ค้นหา Detail/สาเหตุ", placeholder="พิมพ์สาเหตุ...")
        fdf_table = fdf.copy()
        if search_pdr: fdf_table = fdf_table[fdf_table["PDR No."].astype(str).str.contains(search_pdr, case=False, na=False)]
        if search_cust: fdf_table = fdf_table[fdf_table["ชื่อลูกค้า"].astype(str).str.contains(search_cust, case=False, na=False)]
        if search_detail: fdf_table = fdf_table[fdf_table["Detail"].astype(str).str.contains(search_detail, case=False, na=False)]
        fdf_table["วันที่"] = fdf_table["วันที่"].dt.strftime("%d/%m/%Y"); available_cols = [c for c in target_columns if c in fdf_table.columns]
        st.markdown(f"พบข้อมูลทั้งหมด **{len(fdf_table):,}** แถว")
        st.dataframe(fdf_table[available_cols].sort_values("ลำดับที่", ascending=True), use_container_width=True, hide_index=True)

st.caption("Shortage Intelligence Dashboard | Original Visual Style Restored | ข้อมูลครบถ้วน 100%")
