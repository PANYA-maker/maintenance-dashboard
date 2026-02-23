import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# 1. Page Config & Professional Styling
# ======================================
st.set_page_config(
    page_title="Speed Analytics Executive Dashboard",
    page_icon="📉",
    layout="wide"
)

# Custom CSS for Premium Design
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
    
    # Date logic: Flexible date parsing
    df["วันที่"] = pd.to_datetime(df["วันที่"], dayfirst=True, errors="coerce")
    
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

if df["วันที่"].notna().any():
    absolute_min_date = df["วันที่"].min().date()
    absolute_max_date = df["วันที่"].max().date()
    default_start = absolute_max_date - pd.Timedelta(days=6)
    if default_start < absolute_min_date:
        default_start = absolute_min_date
else:
    absolute_min_date = pd.Timestamp.today().date()
    absolute_max_date = pd.Timestamp.today().date()
    default_start = absolute_max_date

date_range = st.sidebar.date_input(
    "📅 เลือกช่วงวันที่",
    value=[default_start, absolute_max_date],
    min_value=absolute_min_date,
    max_value=absolute_max_date
)

def get_opts(col):
    return sorted([o for o in df[col].unique() if o != ""])

f_machines = st.sidebar.multiselect("🏭 เครื่องจักร", get_opts("เครื่องจักร"))
f_shifts = st.sidebar.multiselect("⏱ กะ", get_opts("กะ"))

# Apply Global Filters
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
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
    st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (แยกตามเครื่องจักร)")
    freq_opt = st.selectbox("เลือกความถี่กราฟ:", options=["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"], index=1)
    
    trend_df = f_df.copy()
    trend_df['Val'] = trend_df.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
    
    if freq_opt == "รายสัปดาห์":
        # logic: Sunday as the first day of the week
        # (dt.weekday + 1) % 7 calculates how many days back to get to Sunday (Monday=0...Sunday=6)
        trend_df['Week_Start'] = trend_df['วันที่'] - pd.to_timedelta((trend_df['วันที่'].dt.weekday + 1) % 7, unit='D')
        res_trend = trend_df.groupby(['Week_Start', 'เครื่องจักร'])['Val'].sum().reset_index()
        res_trend['Label'] = res_trend['Week_Start'].dt.strftime('%d/%m (Sun)')
        res_trend = res_trend.sort_values(['Week_Start', 'เครื่องจักร'])
    else:
        m_map = {"รายวัน": "D", "รายเดือน": "MS", "รายปี": "YS"}
        res_trend = trend_df.groupby(['เครื่องจักร', pd.Grouper(key='วันที่', freq=m_map[freq_opt])])['Val'].sum().reset_index()
        fmt = {"รายวัน": "%d/%m/%y", "รายเดือน": "%m/%Y", "รายปี": "%Y"}
        res_trend['Label'] = res_trend['วันที่'].dt.strftime(fmt[freq_opt])

    # Trend Chart: Grouped bar by machine, colors based on values
    fig_trend = go.Figure()
    machine_colors_fixed = {"BHS": "#F1C40F", "BSH": "#F1C40F", "YUELI": "#2ECC71", "ISOWA": "#3498DB"}
    backup_pal = px.colors.qualitative.Pastel
    
    m_list_final = sorted(res_trend['เครื่องจักร'].unique())
    for i, m in enumerate(m_list_final):
        m_data = res_trend[res_trend['เครื่องจักร'] == m]
        # Label colors: Green if positive, Red if negative
        text_colors = m_data['Val'].apply(lambda x: '#2ecc71' if x >= 0 else '#e74c3c').tolist()
        
        fig_trend.add_trace(go.Bar(
            x=m_data['Label'], y=m_data['Val'], name=m,
            marker_color=machine_colors_fixed.get(m.upper(), backup_pal[i % len(backup_pal)]),
            text=m_data['Val'].round(0).astype(int),
            textposition='outside',
            textfont=dict(size=14, color=text_colors, family="Arial Black"),
            hovertemplate="เครื่อง: " + m + "<br>เวลา: %{x}<br>ค่า: %{y}<extra></extra>"
        ))
    
    fig_trend.update_layout(height=500, barmode='group', template="plotly_white", margin=dict(l=20, r=20, t=30, b=20),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5))
    st.plotly_chart(fig_trend, use_container_width=True)

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
            total_orders_exec = len(f_df)
            for _, row in status_summary.iterrows():
                pct = (row['count'] / total_orders_exec) * 100
                st.write(f"**{row['Speed เทียบแผน']}:** {row['count']:,} ออเดอร์ ({pct:.1f}%)")
            st.info(f"รวมทั้งหมด: {total_orders_exec:,} รายการ")

# --- TAB 2: LOSS & ROOT CAUSE ---
with tab_analysis:
    ns_loss_all = f_df[(f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง") & (f_df["Diff เวลา"] < 0)].copy()
    if not ns_loss_all.empty:
        # Executive Summary Calculation
        total_loss_exec = int(round(abs(ns_loss_all["Diff เวลา"].sum())))
        num_late_exec = len(ns_loss_all)
        pareto_full_exec = ns_loss_all.groupby("กรุ๊ปปัญหา")["Diff เวลา"].sum().abs().reset_index()
        top_prob_exec = pareto_full_exec.sort_values(by="Diff เวลา", ascending=False).iloc[0]
        top_10_exec = ns_loss_all.sort_values(by="Diff เวลา", ascending=True).head(10)
        total_lost_top10_exec = int(round(abs(top_10_exec["Diff เวลา"].sum())))

        st.markdown(f"""
        <div class="insight-box">
            <h4 style="color:#c0392b; margin-top:0; font-weight:800;">💡 Executive Summary: บทวิเคราะห์ความสูญเสียสปีด</h4>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <p style="margin-bottom:8px;"><b>📉 ผลกระทบเชิงแผนงาน:</b></p>
                    <ul style="margin-bottom:0; font-size:15px;">
                        <li>พบออเดอร์ล่าช้าสะสม <b>{num_late_exec:,} รายการ</b> สูญเสียเวลารวม <b>{total_loss_exec:,} นาที</b></li>
                        <li>กลุ่มวิกฤต (Top 10) สร้างความสูญเสียถึง <b>{total_lost_top10_exec:,} นาที</b> ({int(round(total_lost_top10_exec/total_loss_exec*100))}% ของทั้งหมด)</li>
                    </ul>
                </div>
                <div>
                    <p style="margin-bottom:8px;"><b>🏭 สาเหตุวิกฤต (Root Cause):</b></p>
                    <ul style="margin-bottom:0; font-size:15px;">
                        <li><b>ปัญหาหลัก:</b> <b>"{top_prob_exec['กรุ๊ปปัญหา'] if top_prob_exec['กรุ๊ปปัญหา'] != '' else 'ไม่ระบุ'}"</b> กินเวลาไปถึง <b>{int(round(top_prob_exec['Diff เวลา'])):,} นาที</b></li>
                        <li><b>ข้อเสนอแนะ:</b> ควรตรวจสอบคอขวดในกลุ่มปัญหานี้เป็นอันดับแรกเพื่อดึงประสิทธิภาพกลับมา</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📈 Pareto: กลุ่มปัญหาที่สร้างความสูญเสียสะสม (นาที)")
        pareto_data_exec = pareto_full_exec[pareto_full_exec["กรุ๊ปปัญหา"] != ""].sort_values(by="Diff เวลา", ascending=True).tail(10)
        fig_pareto_exec = px.bar(pareto_data_exec, x="Diff เวลา", y="กรุ๊ปปัญหา", orientation='h', 
                            text=pareto_data_exec["Diff เวลา"].round(0).astype(int), 
                            color="Diff เวลา", color_continuous_scale="Reds")
        fig_pareto_exec.update_layout(height=450, template="plotly_white", showlegend=False, xaxis_title="นาทีสะสม", yaxis_title=None, coloraxis_showscale=False)
        st.plotly_chart(fig_pareto_exec, use_container_width=True)
            
        st.markdown("#### 📋 10 รายการออเดอร์ที่มีความล่าช้าสูงสุด (Critical Loss)")
        show_cols_exec = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top_exec = top_10_exec[show_cols_exec].copy()
        for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            display_top_exec[c] = display_top_exec[c].round(0).astype(int)
        st.dataframe(display_top_exec, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ ไม่พบออเดอร์ที่มีความล่าช้าในช่วงเวลานี้")

# --- TAB 3: DATA LOGS ---
with tab_logs:
    st.markdown("### 📋 วิเคราะห์รายละเอียดรายเครื่องจักรและออเดอร์")
    col_a_log, col_b_log = st.columns(2)
    with col_a_log:
        st.markdown("#### 📦 สัดส่วนออเดอร์แยกตามเครื่องจักร")
        bar_df_log = f_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
        bar_df_log['Total'] = bar_df_log.groupby('เครื่องจักร')['C'].transform('sum')
        bar_df_log['Pct'] = (bar_df_log['C'] / bar_df_log['Total'] * 100).round(1)
        bar_df_log['Label'] = bar_df_log.apply(lambda r: f"{int(r['C'])} ({r['Pct']}%)", axis=1)
        fig_bar_log = px.bar(bar_df_log, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack",
                         color_discrete_sequence=px.colors.qualitative.Pastel, text='Label')
        fig_bar_log.update_layout(height=400, template="plotly_white", margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), uniformtext_minsize=8, uniformtext_mode='hide')
        fig_bar_log.update_traces(textposition='inside', insidetextanchor='middle', marker_line_color='white', marker_line_width=1.5)
        st.plotly_chart(fig_bar_log, use_container_width=True)

    with col_b_log:
        st.markdown("#### 🛑 สาเหตุการจอดเครื่องสะสม")
        pie_stop_log = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
        fig_stop_log = px.pie(pie_stop_log, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.6, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_stop_log.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        fig_stop_log.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
        st.plotly_chart(fig_stop_log, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔍 ตัวกรองและรายการออเดอร์ (Data Logs)")
    with st.expander("🛠 เครื่องมือกรองตาราง (Table Filters)", expanded=True):
        c1_t, c2_t, c3_t = st.columns(3)
        with c1_t: search_pdr_t = st.text_input("ค้นหา PDR:", placeholder="พิมพ์รหัส PDR...")
        with c2_t: filter_prob_t = st.multiselect("กรองกรุ๊ปปัญหา:", options=get_opts("กรุ๊ปปัญหา"))
        with c3_t: filter_speed_t = st.multiselect("กรอง Speed เทียบแผน:", options=get_opts("Speed เทียบแผน") if "Speed เทียบแผน" in f_df.columns else [])

    log_df_t = f_df.copy()
    if search_pdr_t: log_df_t = log_df_t[log_df_t["PDR"].str.contains(search_pdr_t, case=False, na=False)]
    if filter_prob_t: log_df_t = log_df_t[log_df_t["กรุ๊ปปัญหา"].isin(filter_prob_t)]
    if filter_speed_t: log_df_t = log_df_t[log_df_t["Speed เทียบแผน"].isin(filter_speed_t)]

    log_cols_t = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    display_df_t = log_df_t[[c for c in log_cols_t if c in log_df_t.columns]].sort_values("วันที่", ascending=False).copy()
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        if c in display_df_t.columns: display_df_t[c] = display_df_t[c].round(0).astype(int)
    
    def highlight_rows_t(row):
        color = 'background-color: #ffebee' if row['Diff เวลา'] < -5 else ''
        return [color] * len(row)
    st.dataframe(display_df_t.style.apply(highlight_rows_t, axis=1), use_container_width=True, height=600)

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Dashboard © 2026</div>", unsafe_allow_html=True)
