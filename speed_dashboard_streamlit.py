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

    # Text Logic (Keep original content from GS)
    text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2", "Speed เทียบแผน"]
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
# 3. Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")
if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

max_date = df["วันที่"].max() if df["วันที่"].notna().any() else pd.Timestamp.today()
min_date = max_date - pd.Timedelta(days=6)
date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_date, max_date])

def get_opts(col):
    return sorted([o for o in df[col].unique() if o != ""])

f_machines = st.sidebar.multiselect("🏭 เครื่องจักร", get_opts("เครื่องจักร"))
f_shifts = st.sidebar.multiselect("⏱ กะ", get_opts("กะ"))
f_speed_status = st.sidebar.multiselect("📊 Speed เทียบแผน", get_opts("Speed เทียบแผน"))

# Apply Filters
if len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    f_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    f_df = df.copy()

if f_machines: f_df = f_df[f_df["เครื่องจักร"].isin(f_machines)]
if f_shifts: f_df = f_df[f_df["กะ"].isin(f_shifts)]
if f_speed_status: f_df = f_df[f_df["Speed เทียบแผน"].isin(f_speed_status)]

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
# 5. Dashboard Layout (3 Tabs)
# ======================================
tab_overview, tab_analysis, tab_logs = st.tabs([
    "📊 Executive Overview", 
    "🚩 Loss Root Cause", 
    "📋 Detailed Logs"
])

# --- TAB 1: EXECUTIVE OVERVIEW ---
with tab_overview:
    st.markdown("### 📊 Performance KPI Summary")
    
    def kpi_card(title, bg, order, time):
        return f"""
        <div style="background:{bg}; padding:25px; border-radius:15px; color:#fff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 10px;">
            <h4 style="text-align:center; margin:0 0 15px 0; font-size:18px; font-weight:800; text-transform:uppercase; letter-spacing: 1px;">{title}</h4>
            <div style="display:flex; gap:15px; justify-content:space-between;">
                <div style="background:rgba(255,255,255,0.25); padding:12px; border-radius:12px; flex:1; text-align:center; backdrop-filter: blur(5px);">
                    <div style="font-size:12px; opacity:0.9; font-weight: 500;">Order</div>
                    <div style="font-size:28px; font-weight:800;">{order:,}</div>
                </div>
                <div style="background:rgba(255,255,255,0.25); padding:12px; border-radius:12px; flex:1; text-align:center; backdrop-filter: blur(5px);">
                    <div style="font-size:12px; opacity:0.9; font-weight: 500;">Time Min</div>
                    <div style="font-size:28px; font-weight:800;">{time:+,}</div>
                </div>
            </div>
        </div>
        """
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("NON-STOP", "#6c5ce7", ns_count, int(round(raw_ns_min))), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("STOP ORDERS", "#e67e22", so_count, int(round(raw_so_min))), unsafe_allow_html=True)
    with c3:
        color = "#27ae60" if overall_time >= 0 else "#c0392b"
        st.markdown(kpi_card("OVERALL SPEED", color, ns_count + so_count, overall_time), unsafe_allow_html=True)

    st.markdown("---")
    
    # Trend Chart
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

    fig_t = go.Figure(go.Bar(
        x=res['Label'], y=res['Val'], 
        marker_color=['#55efc4' if v >= 0 else '#ff7675' for v in res['Val']],
        text=res['Val'].round(0).astype(int), textposition='outside'
    ))
    fig_t.update_layout(height=400, template="plotly_white", margin=dict(l=20, r=20, t=10, b=20), xaxis_title=None)
    st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("---")
    # Speed Distribution
    st.markdown("#### 📊 Speed Performance Distribution")
    if "Speed เทียบแผน" in f_df.columns:
        status_summary = f_df["Speed เทียบแผน"].value_counts().reset_index()
        fig_pie = px.pie(status_summary, names="Speed เทียบแผน", values="count", hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(height=450, margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 2: LOSS & ROOT CAUSE ---
with tab_analysis:
    st.markdown("### 🚩 วิเคราะห์ความสูญเสียสปีด (Loss Analysis)")
    ns_loss = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()
    
    if not ns_loss.empty:
        # Pareto Chart (Sum of Loss by Problem Group)
        st.markdown("#### 📈 Pareto: กลุ่มปัญหาที่สร้างความสูญเสียสะสม (นาที)")
        pareto_data = ns_loss[ns_loss["Diff เวลา"] < 0].groupby("กรุ๊ปปัญหา")["Diff เวลา"].sum().abs().reset_index()
        pareto_data = pareto_data[pareto_data["กรุ๊ปปัญหา"] != ""].sort_values(by="Diff เวลา", ascending=False).head(8)
        
        if not pareto_data.empty:
            # ใช้จำนวนเต็มในกราฟ Pareto เพื่อความสอดคล้อง
            fig_pareto = px.bar(
                pareto_data, 
                x="Diff เวลา", 
                y="กรุ๊ปปัญหา", 
                orientation='h', 
                text=pareto_data["Diff เวลา"].round(0).astype(int), # แสดงตัวเลขปัดเศษ
                color="Diff เวลา", 
                color_continuous_scale="Reds"
            )
            fig_pareto.update_layout(height=400, template="plotly_white", showlegend=False, xaxis_title="นาทีสะสม (ปัดเศษ)", yaxis_title=None)
            st.plotly_chart(fig_pareto, use_container_width=True)
            
        # Top 10 Critical Table (Individual Orders)
        st.markdown("#### 📋 10 รายการออเดอร์ที่มีความล่าช้าสูงสุด (Critical Loss)")
        top_10 = ns_loss.sort_values(by="Diff เวลา", ascending=True).head(10)
        show_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top = top_10[show_cols].copy()
        
        # ปัดเศษเป็นจำนวนเต็ม
        for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            if c in display_top.columns:
                display_top[c] = display_top[c].round(0).astype(int)
        
        st.dataframe(display_top, use_container_width=True, hide_index=True)
        
        # Executive Insights
        total_lost_min = int(round(abs(top_10["Diff เวลา"].sum())))
        st.error(f"""
        **💡 Executive Insights (สรุปข้อมูล 10 อันดับวิกฤต)**
        * ในออเดอร์ 10 รายการที่ช้าที่สุดนี้ มีเวลาที่สูญเสียรวมทั้งสิ้น **{total_lost_min:,} นาที**
        * ตัวเลขในกราฟ Pareto ด้านบนแสดง **"ผลรวมสะสม"** ของปัญหาทั้งหมดในช่วงเวลาที่เลือก ส่วนตารางด้านบนแสดง **"รายการเดี่ยว"** ที่วิกฤตที่สุดครับ
        """)
    else:
        st.info("ℹ️ ไม่พบออเดอร์ประเภท 'ไม่จอดเครื่อง' ที่ล่าช้าในช่วงเวลานี้")

# --- TAB 3: DATA LOGS ---
with tab_logs:
    st.markdown("### 📋 ข้อมูลรายออเดอร์แบบละเอียด (Data Logs)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📦 สัดส่วนลักษณะ Order ความยาว")
        bar_df = f_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
        fig_bar = px.bar(bar_df, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_bar.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_b:
        st.markdown("#### 🛑 สาเหตุการจอดเครื่องสะสม")
        pie_stop = f_df[f_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
        fig_stop = px.pie(pie_stop, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_stop.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_stop, use_container_width=True)

    st.markdown("---")
    log_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    display_df = f_df[[c for c in log_cols if c in f_df.columns]].sort_values("วันที่", ascending=False).copy()
    
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        if c in display_df.columns:
            display_df[c] = display_df[c].round(0).astype(int)

    def highlight_rows(row):
        color = 'background-color: #ffebee' if row['Diff เวลา'] < -5 else ''
        return [color] * len(row)

    st.dataframe(display_df.style.apply(highlight_rows, axis=1), use_container_width=True, height=600)

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Executive Dashboard © 2026</div>", unsafe_allow_html=True)
