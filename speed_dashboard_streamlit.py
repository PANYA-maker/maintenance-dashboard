import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# 1. Page Config & Premium CSS
# ======================================
st.set_page_config(
    page_title="Speed Analytics Executive Dashboard",
    page_icon="📉",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #f4f7f9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        padding: 0 20px;
        font-weight: 600;
        color: #4a5568;
    }
    .stTabs [aria-selected="true"] {
        color: #ff4b4b;
        border-bottom: 3px solid #ff4b4b;
    }
    .insight-box {
        background-color: #fff5f5;
        border-left: 5px solid #ff4b4b;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .filter-section {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ======================================
# 2. Data Loading & Cleaning
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

@st.cache_data(ttl=300)
def load_and_clean_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    try:
        df = pd.read_csv(url)
    except:
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    
    # Date logic
    df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
    if df["วันที่"].isna().all():
        df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

    # Numeric logic
    numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Text Logic
    text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2", "Speed เทียบแผน", "PDR"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            df[col] = df[col].replace(['nan', 'NaN', 'None', 'null'], '')
            
    return df

df = load_and_clean_data()

if df.empty:
    st.warning("⚠️ ไม่พบข้อมูล กรุณาตรวจสอบการเชื่อมต่อ Google Sheets")
    st.stop()

# ======================================
# 3. Sidebar Filters (Global)
# ======================================
st.sidebar.header("🔎 ตัวกรองหลัก")
if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

max_date = df["วันที่"].max() if df["วันที่"].notna().any() else pd.Timestamp.today()
min_date = max_date - pd.Timedelta(days=6)
date_range = st.sidebar.date_input("📅 ช่วงวันที่", [min_date, max_date])

def get_opts(col):
    return sorted([o for o in df[col].unique() if o != ""])

f_machines = st.sidebar.multiselect("🏭 เครื่องจักร", get_opts("เครื่องจักร"))
f_shifts = st.sidebar.multiselect("⏱ กะ", get_opts("กะ"))

# Apply Global Filters
if len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    f_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    f_df = df.copy()

if f_machines: f_df = f_df[f_df["เครื่องจักร"].isin(f_machines)]
if f_shifts: f_df = f_df[f_df["กะ"].isin(f_shifts)]

# ======================================
# 4. KPI Calculation
# ======================================
ns_mask = (f_df["Checked-2"].str.upper() == "YES") & (f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
ns_count = len(f_df[ns_mask])
raw_ns_min = f_df.loc[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

so_mask = (f_df["Checked-2"].str.upper() == "YES") & (f_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
so_count = len(f_df[so_mask])
raw_so_min = f_df.loc[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

overall_time = int(round(raw_ns_min + raw_so_min))

# ======================================
# 5. Tabs Layout
# ======================================
tab_overview, tab_analysis, tab_logs = st.tabs([
    "📊 Executive Overview", 
    "🚩 Loss Root Cause", 
    "📋 Detailed Logs"
])

# --- TAB 1: EXECUTIVE OVERVIEW ---
with tab_overview:
    st.markdown("### 📊 Performance KPI Summary")
    
    c1, c2, c3 = st.columns(3)
    def kpi_card(title, bg, order, time):
        return f"""
        <div style="background:{bg}; padding:20px; border-radius:15px; color:#fff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 10px;">
            <h4 style="text-align:center; margin:0 0 15px 0; font-size:18px; font-weight:800; text-transform:uppercase;">{title}</h4>
            <div style="display:flex; gap:10px; justify-content:space-between;">
                <div style="background:rgba(255,255,255,0.25); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Order</div>
                    <div style="font-size:24px; font-weight:800;">{order:,}</div>
                </div>
                <div style="background:rgba(255,255,255,0.25); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Time Min</div>
                    <div style="font-size:24px; font-weight:800;">{time:+,}</div>
                </div>
            </div>
        </div>
        """
    with c1: st.markdown(kpi_card("NON-STOP", "#6c5ce7", ns_count, int(round(raw_ns_min))), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("STOP ORDERS", "#e67e22", so_count, int(round(raw_so_min))), unsafe_allow_html=True)
    with c3:
        color = "#27ae60" if overall_time >= 0 else "#c0392b"
        st.markdown(kpi_card("OVERALL SPEED", color, ns_count + so_count, overall_time), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📈 แนวโน้ม OVERALL SPEED")
    freq = st.selectbox("เลือกความถี่กราฟ:", options=["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"], index=1)
    
    trend_df = f_df.copy()
    trend_df['Val'] = trend_df.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
    
    if freq == "รายสัปดาห์":
        trend_df['ISO_Week'] = trend_df['วันที่'].dt.isocalendar().week
        res = trend_df.groupby('ISO_Week')['Val'].sum().reset_index()
        res['Label'] = res['ISO_Week'].apply(lambda x: f"WEEK {x}")
    else:
        m_map = {"รายวัน": "D", "รายเดือน": "MS", "รายปี": "YS"}
        res = trend_df.set_index('วันที่')['Val'].resample(m_map[freq]).sum().reset_index()
        fmt = {"รายวัน": "%d/%m/%y", "รายเดือน": "%m/%Y", "รายปี": "%Y"}
        res['Label'] = res['วันที่'].dt.strftime(fmt[freq])

    fig_t = go.Figure(go.Bar(x=res['Label'], y=res['Val'], marker_color=['#55efc4' if v >= 0 else '#ff7675' for v in res['Val']], text=res['Val'].round(0).astype(int), textposition='outside'))
    fig_t.update_layout(height=400, template="plotly_white", margin=dict(l=20, r=20, t=10, b=20), xaxis_title=None)
    st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("---")
    col_pie, col_sum = st.columns([1.5, 1])
    with col_pie:
        st.markdown("#### 📊 Speed Performance Distribution")
        if "Speed เทียบแผน" in f_df.columns:
            status_summary = f_df["Speed เทียบแผน"].value_counts().reset_index()
            fig_pie = px.pie(status_summary, names="Speed เทียบแผน", values="count", hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
            fig_pie.update_traces(textinfo='percent', marker=dict(line=dict(color='#ffffff', width=2)))
            st.plotly_chart(fig_pie, use_container_width=True)
    with col_sum:
        st.markdown("#### 📝 สรุปสัดส่วนประสิทธิภาพ")
        if not f_df.empty:
            total = len(f_df)
            for _, row in status_summary.iterrows():
                pct = (row['count'] / total) * 100
                st.write(f"**{row['Speed เทียบแผน']}:** {row['count']:,} ออเดอร์ ({pct:.1f}%)")
            st.info(f"รวมทั้งสิ้น: {total:,} รายการ")

# --- TAB 2: LOSS & ROOT CAUSE ---
with tab_analysis:
    ns_loss_all = f_df[(f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง") & (f_df["Diff เวลา"] < 0)].copy()
    if not ns_loss_all.empty:
        total_loss_all_min = int(round(abs(ns_loss_all["Diff เวลา"].sum())))
        num_late_orders = len(ns_loss_all)
        pareto_full = ns_loss_all.groupby("กรุ๊ปปัญหา")["Diff เวลา"].sum().abs().reset_index()
        top_prob = pareto_full.sort_values(by="Diff เวลา", ascending=False).iloc[0]
        top_10 = ns_loss_all.sort_values(by="Diff เวลา", ascending=True).head(10)
        total_lost_top10 = int(round(abs(top_10["Diff เวลา"].sum())))
        
        st.markdown(f"""
        <div class="insight-box">
            <h4 style="color:#c0392b; margin-top:0; font-weight:800;">💡 Executive Summary: บทวิเคราะห์ความสูญเสียสปีด</h4>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <p style="margin-bottom:8px;"><b>📉 ผลกระทบเชิงแผนงาน:</b></p>
                    <ul style="margin-bottom:0; font-size:15px;">
                        <li>พบออเดอร์ล่าช้าสะสม <b>{num_late_orders:,} รายการ</b> สูญเสียเวลารวม <b>{total_loss_all_min:,} นาที</b></li>
                        <li>กลุ่มวิกฤต (Top 10) สร้างความสูญเสียถึง <b>{total_lost_top10:,} นาที</b> ({int(round(total_lost_top10/total_loss_all_min*100))}% ของทั้งหมด)</li>
                    </ul>
                </div>
                <div>
                    <p style="margin-bottom:8px;"><b>🏭 สาเหตุวิกฤต (Root Cause):</b></p>
                    <ul style="margin-bottom:0; font-size:15px;">
                        <li><b>ปัญหาหลัก:</b> <b>"{top_prob['กรุ๊ปปัญหา'] if top_prob['กรุ๊ปปัญหา'] != '' else 'ไม่ระบุ'}"</b> กินเวลาไป <b>{int(round(top_prob['Diff เวลา'])):,} นาที</b></li>
                        <li><b>ข้อเสนอแนะ:</b> ควรจัดลำดับความสำคัญในการปรับจูนสปีดที่กลุ่มปัญหาหลักเป็นอันดับแรก</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📈 Pareto: กลุ่มปัญหาที่สร้างความสูญเสียสะสม (นาที)")
        pareto_data = pareto_full[pareto_full["กรุ๊ปปัญหา"] != ""].sort_values(by="Diff เวลา", ascending=True).tail(8)
        fig_pareto = px.bar(pareto_data, x="Diff เวลา", y="กรุ๊ปปัญหา", orientation='h', text=pareto_data["Diff เวลา"].round(0).astype(int), color="Diff เวลา", color_continuous_scale="Reds")
        fig_pareto.update_layout(height=450, template="plotly_white", showlegend=False, xaxis_title="นาทีสะสม", yaxis_title=None, coloraxis_showscale=False)
        st.plotly_chart(fig_pareto, use_container_width=True)
            
        st.markdown("#### 📋 10 รายการออเดอร์ที่มีความล่าช้าสูงสุด (Critical Loss)")
        show_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top = top_10[show_cols].copy()
        for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            display_top[c] = display_top[c].round(0).astype(int)
        st.dataframe(display_top, use_container_width=True, hide_index=True)

# --- TAB 3: DATA LOGS & ENHANCED CHARTS ---
with tab_logs:
    st.markdown("### 📋 วิเคราะห์รายละเอียดรายเครื่องจักรและออเดอร์")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📦 สัดส่วนออเดอร์แยกตามเครื่องจักร")
        if "เครื่องจักร" in f_df.columns:
            bar_df = f_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
            fig_bar = px.bar(
                bar_df, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", 
                orientation="h", barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                text_auto=True
            )
            fig_bar.update_layout(
                height=350, template="plotly_white", 
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                xaxis_title="จำนวนออเดอร์"
            )
            fig_bar.update_traces(marker_line_color='white', marker_line_width=1, opacity=0.9)
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.markdown("#### 🛑 สาเหตุการจอดเครื่องสะสม")
        if "ลักษณะ เวลาหยุดเครื่อง" in f_df.columns:
            pie_stop = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
            fig_stop = px.pie(
                pie_stop, names="ลักษณะ เวลาหยุดเครื่อง", values="C", 
                hole=0.6, color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_stop.update_layout(
                height=350, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            fig_stop.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
            st.plotly_chart(fig_stop, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔍 ตัวกรองและรายการออเดอร์ (Data Logs)")
    
    # --- TABLE FILTER SECTION ---
    with st.expander("🛠 เครื่องมือกรองตาราง (Table Filters)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            search_pdr = st.text_input("ค้นหา PDR (พิมพ์รหัส):", placeholder="เช่น PDR2602...")
        with c2:
            filter_prob = st.multiselect("กรองตามกรุ๊ปปัญหา:", options=get_opts("กรุ๊ปปัญหา"))
        with c3:
            filter_speed = st.multiselect("กรองตาม Speed เทียบแผน:", options=get_opts("Speed เทียบแผน"))

    # Apply Table Filters
    log_df = f_df.copy()
    if search_pdr:
        log_df = log_df[log_df["PDR"].str.contains(search_pdr, case=False, na=False)]
    if filter_prob:
        log_df = log_df[log_df["กรุ๊ปปัญหา"].isin(filter_prob)]
    if filter_speed:
        log_df = log_df[log_df["Speed เทียบแผน"].isin(filter_speed)]

    # Final Data Preparation
    log_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    display_df = log_df[[c for c in log_cols if c in log_df.columns]].sort_values("วันที่", ascending=False).copy()
    
    # ปัดเศษ
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        if c in display_df.columns:
            display_df[c] = display_df[c].round(0).astype(int)

    # Styling Table
    def highlight_rows(row):
        color = 'background-color: #ffebee' if row['Diff เวลา'] < -5 else ''
        return [color] * len(row)

    st.dataframe(display_df.style.apply(highlight_rows, axis=1), use_container_width=True, height=600)

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Executive Dashboard © 2026</div>", unsafe_allow_html=True)
