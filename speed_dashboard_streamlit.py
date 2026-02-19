import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# 1. Page Config
# ======================================
st.set_page_config(
    page_title="Speed – Performance Dashboard",
    page_icon="📉",
    layout="wide"
)

# ======================================
# 2. Google Sheet Config & Load Data
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
    st.warning("ไม่พบข้อมูล กรุณาตรวจสอบ Google Sheet")
    st.stop()

# ======================================
# 3. Data Cleaning (จัดการทั้งตัวเลขและตัวหนังสือ)
# ======================================
df.columns = df.columns.str.strip()

# จัดการวันที่
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
     df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

# จัดการตัวเลข
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# จัดการตัวหนังสือ (สาเหตุจาก, กรุ๊ปปัญหา, รายละเอียด) ให้แสดงผลถูกต้อง
text_target_cols = [
    "เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", 
    "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", 
    "รายละเอียด", "Checked-2", "PDR", "Flute", "Speed เทียบแผน"
]
for col in text_target_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None', 'null', '0', '0.0'], '')
        df[col] = df[col].str.strip()

# ======================================
# 4. Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")
if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

max_date = df["วันที่"].max() if df["วันที่"].notna().any() else pd.Timestamp.today()
min_date = max_date - pd.Timedelta(days=6)
date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_date, max_date])

def multi_filter(label, col):
    if col in df.columns:
        valid_opts = sorted([o for o in df[col].unique() if o != ""])
        return st.sidebar.multiselect(label, valid_opts)
    return []

f_machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
f_shifts = multi_filter("⏱ กะ", "กะ")
f_speed_status = multi_filter("📊 Speed เทียบแผน", "Speed เทียบแผน")

# Apply Filters
if len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    filtered_df = df.copy()

if f_machines: filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(f_machines)]
if f_shifts: filtered_df = filtered_df[filtered_df["กะ"].isin(f_shifts)]
if f_speed_status: filtered_df = filtered_df[filtered_df["Speed เทียบแผน"].isin(f_speed_status)]

# ======================================
# 5. KPI CALCULATION
# ======================================
# 1. NON-STOP
ns_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
ns_count = len(filtered_df[ns_mask])
raw_ns_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# 2. STOP ORDERS
so_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
so_count = len(filtered_df[so_mask])
raw_so_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# 3. OVERALL
overall_time = int(round(raw_ns_min + raw_so_min))

# ======================================
# 6. TABBED LAYOUT (หัวใจของการแบ่งหน้า)
# ======================================
tab_overview, tab_loss, tab_logs = st.tabs([
    "📈 Performance Overview", 
    "🚩 Loss Analysis & Insights", 
    "📋 Detailed Logs"
])

# --- TAB 1: OVERVIEW ---
with tab_overview:
    st.markdown("### 📊 Speed – Performance Overview")
    
    def kpi_card(title, bg, order, time):
        return f"""
        <div style="background:{bg}; padding:20px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">
            <h4 style="text-align:center; margin:0 0 15px 0; font-size:18px; font-weight:800; text-transform:uppercase;">{title}</h4>
            <div style="display:flex; gap:10px; justify-content:space-between;">
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Order</div>
                    <div style="font-size:24px; font-weight:800;">{order:,}</div>
                </div>
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Time Min</div>
                    <div style="font-size:24px; font-weight:800;">{time:+,}</div>
                </div>
            </div>
        </div>
        """
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("NON-STOP", "#8e44ad", ns_count, int(round(raw_ns_min))), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("STOP ORDERS", "#d35400", so_count, int(round(raw_so_min))), unsafe_allow_html=True)
    with c3:
        color = "#27ae60" if overall_time >= 0 else "#c0392b"
        st.markdown(kpi_card("OVERALL SPEED", color, ns_count + so_count, overall_time), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (Time Trend Analysis)")
    
    # ดึงตัวเลือกความถี่กลับมา
    freq_col1, freq_col2 = st.columns([1, 4])
    with freq_col1:
        freq_option = st.selectbox("เลือกความถี่ของกราฟ:", options=["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"], index=1)

    trend_data = filtered_df.copy()
    trend_data['Val'] = trend_data.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
    
    if freq_option == "รายสัปดาห์":
        trend_data['ISO_Year'] = trend_data['วันที่'].dt.isocalendar().year
        trend_data['ISO_Week'] = trend_data['วันที่'].dt.isocalendar().week
        res = trend_data.groupby(['ISO_Year', 'ISO_Week'])['Val'].sum().reset_index()
        res['Label'] = res.apply(lambda x: f"WEEK {x['ISO_Week']}", axis=1)
        res = res.sort_values(['ISO_Year', 'ISO_Week'])
    else:
        m_map = {"รายวัน": "D", "รายเดือน": "MS", "รายปี": "YS"}
        res = trend_data.set_index('วันที่')['Val'].resample(m_map[freq_option]).sum().reset_index()
        fmt = {"รายวัน": "%d/%m/%y", "รายเดือน": "%m/%Y", "รายปี": "%Y"}
        res['Label'] = res['วันที่'].dt.strftime(fmt[freq_option])

    fig_t = go.Figure(go.Bar(x=res['Label'], y=res['Val'], marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res['Val']], text=res['Val'].round(0).astype(int), textposition='outside'))
    fig_t.update_layout(height=450, template="plotly_white", margin=dict(l=20, r=20, t=10, b=20), xaxis_title="ช่วงเวลา", yaxis_title="Overall Speed (Min)")
    st.plotly_chart(fig_t, use_container_width=True)

# --- TAB 2: LOSS ANALYSIS ---
with tab_loss:
    st.markdown("#### 🚩 10 อันดับออเดอร์ไม่จอดเครื่องที่ช้ากว่าแผนมากที่สุด")
    
    ns_loss_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()
    
    if not ns_loss_df.empty:
        top_10 = ns_loss_df.sort_values(by="Diff เวลา", ascending=True).head(10)
        
        # Executive Insights
        total_lost = abs(top_10["Diff เวลา"].sum())
        main_prob = top_10[top_10["กรุ๊ปปัญหา"] != ""]["กรุ๊ปปัญหา"].value_counts().idxmax() if not top_10[top_10["กรุ๊ปปัญหา"] != ""].empty else "ไม่ระบุ"
        
        st.error(f"""
        **💡 Executive Insights (สรุปข้อมูล 10 อันดับที่ช้าที่สุด)**
        * **⚠️ ความสูญเสียรวม:** เฉพาะ 10 รายการนี้เสียเวลาสะสมรวม **{total_lost:,.0f} นาที** จากสปีดที่ตกต่ำกว่าแผน
        * **🏭 สาเหตุวิกฤต:** ปัญหาส่วนใหญ่จัดอยู่ในกลุ่ม **"{main_prob}"** ซึ่งควรตรวจสอบความพร้อมของเครื่องจักรหรือวัตถุดิบ
        * **🔍 ข้อแนะนำ:** ตรวจสอบช่อง "รายละเอียด" ของรายการเหล่านี้เพื่อหาวิธีป้องกันเชิงเทคนิค
        """)
        
        # Table
        show_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top = top_10[show_cols].copy()
        for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            display_top[c] = display_top[c].round(0).astype(int)
        
        st.dataframe(display_top, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบออเดอร์ประเภท 'ไม่จอดเครื่อง' ที่ล่าช้าในช่วงเวลานี้")

# --- TAB 3: LOGS & CHARTS ---
with tab_logs:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📦 สัดส่วนลักษณะ Order ความยาว")
        bar_df = filtered_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
        fig_b = px.bar(bar_df, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_b, use_container_width=True)
    with col_b:
        st.markdown("#### 🛑 สัดส่วนการหยุดเครื่อง")
        pie_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
        fig_p = px.pie(pie_df, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5)
        fig_p.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 รายละเอียดออเดอร์ทั้งหมด (Data Logs)")
    logs_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    st.dataframe(filtered_df[[c for c in logs_cols if c in filtered_df.columns]].sort_values("วันที่", ascending=False), use_container_width=True, height=500)

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Dashboard © 2026</div>", unsafe_allow_html=True)
