import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed – Interactive Dashboard",
    page_icon="📉",
    layout="wide"
)

# ======================================
# Google Sheet Config
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

# ======================================
# Load Data
# ======================================
@st.cache_data(ttl=300)
def load_data():
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    )
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
# Clean column names & Data
# ======================================
df.columns = df.columns.str.strip()

# ======================================
# Convert Date / Time
# ======================================
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
     df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
df["Stop Time"] = pd.to_datetime(df["Stop Time"], errors="coerce")

# แปลงตัวเลข
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ลบช่องว่างในข้อความ
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].astype(str).str.strip()

# ======================================
# Default Date
# ======================================
if df["วันที่"].notna().any():
    max_date = df["วันที่"].max()
    min_7days = max_date - pd.Timedelta(days=6)
else:
    max_date = pd.Timestamp.today()
    min_7days = max_date

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

date_range = st.sidebar.date_input(
    "📅 เลือกช่วงวันที่",
    [min_7days, max_date]
)

def multi_filter(label, col):
    if col in df.columns:
        return st.sidebar.multiselect(
            label,
            sorted(df[col].dropna().unique())
        )
    return []

machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
shifts = multi_filter("⏱ กะ", "กะ")
speed_status = multi_filter("📊 Speed เทียบแผน", "Speed เทียบแผน")
stop_types = multi_filter("🛑 ลักษณะเวลาหยุดเครื่อง", "ลักษณะ เวลาหยุดเครื่อง")
order_lengths = multi_filter("📦 ลักษณะ Order ความยาว", "ลักษณะ Order ความยาว")

# ======================================
# Apply Filters
# ======================================
if len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1])
    filtered_df = df[
        (df["วันที่"] >= start_dt) &
        (df["วันที่"] <= end_dt)
    ].copy()
else:
    filtered_df = df.copy()

if machines:
    filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(machines)]
if shifts:
    filtered_df = filtered_df[filtered_df["กะ"].isin(shifts)]
if speed_status:
    filtered_df = filtered_df[filtered_df["Speed เทียบแผน"].isin(speed_status)]
if stop_types:
    filtered_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"].isin(stop_types)]
if order_lengths:
    filtered_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"].isin(order_lengths)]

# ======================================
# KPI CALCULATION
# ======================================

# 1. NON-STOP Calculation
non_stop_order = 0
raw_non_stop_minute = 0.0
if "Checked-2" in filtered_df.columns and "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
    cond_ns_count = (
        (filtered_df["Checked-2"].str.upper() == "YES") & 
        (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
    )
    non_stop_order = len(filtered_df[cond_ns_count])
    
    cond_ns_time = (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
    if "Diff เวลา" in filtered_df.columns:
        raw_non_stop_minute = filtered_df.loc[cond_ns_time, "Diff เวลา"].sum()

# 2. STOP ORDERS Calculation
stop_orders_count = 0
raw_stop_orders_time_sum = 0.0
if "Checked-2" in filtered_df.columns and "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
    cond_stop_mask = (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
    cond_stop_yes = (filtered_df["Checked-2"].str.upper() == "YES") & cond_stop_mask
    stop_orders_count = len(filtered_df[cond_stop_yes])

    diff_val = filtered_df.loc[cond_stop_mask, "Diff เวลา"].sum() if "Diff เวลา" in filtered_df.columns else 0
    stop_info_val = filtered_df.loc[cond_stop_mask, "เวลาหยุดข้อมูลเครื่อง"].sum() if "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns else 0
    raw_stop_orders_time_sum = diff_val + stop_info_val

# 3. OVERALL Calculation
overall_speed_time = int(round(raw_non_stop_minute + raw_stop_orders_time_sum))

# สำหรับแสดงในการ์ดแยก
non_stop_minute_display = int(round(raw_non_stop_minute))
stop_orders_time_sum_display = int(round(raw_stop_orders_time_sum))

# ======================================
# KPI DISPLAY
# ======================================
st.markdown("### 📊 Speed – Performance Overview")

def kpi_card_compact(title, bg_color, order_val, minute_val, text_color="#fff", order_label="Order", minute_label="Time Min"):
    return f"""
    <div style="
        background:{bg_color};
        padding:20px 15px;
        border-radius:15px;
        color:{text_color};
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    ">
        <h4 style="text-align:center; margin:0 0 15px 0; font-size:18px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">{title}</h4>
        <div style="display:flex; gap:10px; justify-content:space-between;">
            <div style="
                background:rgba(255,255,255,0.2);
                padding:12px 8px;
                border-radius:12px;
                flex:1;
                text-align:center;
                backdrop-filter: blur(4px);
            ">
                <div style="font-size:12px; font-weight: 500; opacity:0.85; margin-bottom: 4px;">{order_label}</div>
                <div style="font-size:24px; font-weight:800;">{order_val:,}</div>
            </div>
            <div style="
                background:rgba(255,255,255,0.2);
                padding:12px 8px;
                border-radius:12px;
                flex:1;
                text-align:center;
                backdrop-filter: blur(4px);
            ">
                <div style="font-size:12px; font-weight: 500; opacity:0.85; margin-bottom: 4px;">{minute_label}</div>
                <div style="font-size:24px; font-weight:800;">{minute_val:+,}</div>
            </div>
        </div>
    </div>
    """

col_ns, col_so, col_ov = st.columns(3)

with col_ns:
    st.markdown(kpi_card_compact("NON-STOP", "#8e44ad", non_stop_order, non_stop_minute_display), unsafe_allow_html=True)

with col_so:
    st.markdown(kpi_card_compact("STOP ORDERS", "#d35400", stop_orders_count, stop_orders_time_sum_display), unsafe_allow_html=True)

with col_ov:
    overall_bg_color = "#27ae60" if overall_speed_time >= 0 else "#c0392b"
    st.markdown(kpi_card_compact(
        "OVERALL SPEED", 
        overall_bg_color, 
        non_stop_order + stop_orders_count, 
        overall_speed_time
    ), unsafe_allow_html=True)

# ======================================
# TREND CHART: OVERALL SPEED
# ======================================
st.markdown("---")
st.markdown("#### 📈 แนวโน้ม OVERALL SPEED (Time Trend Analysis)")

if not filtered_df.empty and "วันที่" in filtered_df.columns:
    trend_data = filtered_df.copy()
    
    def calc_row_overall(row):
        val = 0.0
        if row['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง":
            val = row['Diff เวลา']
        elif row['ลักษณะ เวลาหยุดเครื่อง'] == "จอดเครื่อง":
            val = row['Diff เวลา'] + row['เวลาหยุดข้อมูลเครื่อง']
        return val

    trend_data['Overall_Contribution'] = trend_data.apply(calc_row_overall, axis=1)

    freq_col1, freq_col2 = st.columns([1, 4])
    with freq_col1:
        freq_option = st.selectbox(
            "เลือกความถี่ของกราฟ:",
            options=["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"],
            index=0
        )

    if freq_option == "รายสัปดาห์":
        trend_data['ISO_Year'] = trend_data['วันที่'].dt.isocalendar().year
        trend_data['ISO_Week'] = trend_data['วันที่'].dt.isocalendar().week
        trend_resampled = trend_data.groupby(['ISO_Year', 'ISO_Week'])['Overall_Contribution'].sum().reset_index()
        trend_resampled['Date_Label'] = trend_resampled.apply(
            lambda x: f"WEEK {x['ISO_Week']}" if trend_resampled['ISO_Year'].nunique() == 1 
            else f"{x['ISO_Year']}-W{x['ISO_Week']:02d}", axis=1
        )
        trend_resampled = trend_resampled.sort_values(['ISO_Year', 'ISO_Week'])
    else:
        freq_map = {"รายวัน": "D", "รายเดือน": "MS", "รายปี": "YS"}
        trend_resampled = trend_data.set_index('วันที่')['Overall_Contribution'].resample(freq_map[freq_option]).sum().reset_index()
        
        if freq_option == "รายวัน":
            trend_resampled['Date_Label'] = trend_resampled['วันที่'].dt.strftime('%d/%m/%Y')
        elif freq_option == "รายเดือน":
            trend_resampled['Date_Label'] = trend_resampled['วันที่'].dt.strftime('%m/%Y')
        else:
            trend_resampled['Date_Label'] = trend_resampled['วันที่'].dt.strftime('%Y')

    fig_trend = go.Figure()
    colors = ['#2ecc71' if val >= 0 else '#e74c3c' for val in trend_resampled['Overall_Contribution']]

    fig_trend.add_trace(go.Bar(
        x=trend_resampled['Date_Label'],
        y=trend_resampled['Overall_Contribution'],
        marker_color=colors,
        text=trend_resampled['Overall_Contribution'].round(0).astype(int), 
        textposition='outside',
        hovertemplate="ช่วงเวลา: %{x}<br>Overall Speed: %{y:.1f} Min<extra></extra>"
    ))

    fig_trend.update_layout(
        title=f"แนวโน้มประสิทธิภาพเวลา ({freq_option})",
        xaxis_title="ช่วงเวลา",
        yaxis_title="Overall Speed (Min)",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        template="plotly_white",
        showlegend=False
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ======================================
# SECTION: TOP 10 NON-STOP PERFORMANCE & INSIGHTS
# ======================================
st.markdown("#### 🏆 10 อันดับออเดอร์ไม่จอดเครื่องที่มีประสิทธิภาพสูงสุด (ประหยัดเวลาได้มากที่สุด)")

# Filter only "ไม่จอดเครื่อง"
non_stop_perf_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()

if not non_stop_perf_df.empty:
    # Sort by Diff เวลา ascending (Most negative first)
    top_10_gain = non_stop_perf_df.sort_values(by="Diff เวลา", ascending=True).head(10)
    
    # Calculate Insights based on Top 10 Gainers
    common_best_group = top_10_gain["กรุ๊ปปัญหา"].value_counts().idxmax()
    best_order_type = top_10_gain["ลักษณะ Order ความยาว"].value_counts().idxmax()
    total_saved_time = abs(top_10_gain["Diff เวลา"].sum())
    avg_speed_increase = (top_10_gain["Actual Speed"] - top_10_gain["Speed Plan"]).mean()

    # --- Executive Insights Block (Placed above the table) ---
    st.info(f"""
    **💡 Executive Insights (สรุปเชิงลึกสำหรับผู้บริหาร)**
    
    จากการวิเคราะห์ออเดอร์ที่ทำเวลาได้ดีกว่าแผน (ติดลบมากที่สุด) 10 อันดับแรก พบประเด็นความสำเร็จดังนี้:
    
    * **🚀 ประสิทธิภาพโดดเด่น:** ออเดอร์กลุ่มนี้สามารถประหยัดเวลาการผลิตรวมได้ถึง **{total_saved_time:,.0f} นาที** เมื่อเทียบกับแผนที่วางไว้
    * **📈 ปัจจัยความเร็ว:** มีการทำความเร็ว Actual Speed สูงกว่าแผนเฉลี่ยถึง **{avg_speed_increase:,.0f} unit/hr** โดยไม่มีการหยุดเครื่อง
    * **📦 รูปแบบงานที่เหมาะสม:** ลักษณะออเดอร์ประเภท **"{best_order_type}"** เป็นกลุ่มที่ทำผลงานได้ดีที่สุดในแง่ของความต่อเนื่องและเสถียรภาพ
    * **✅ จุดแข็งที่พบ:** ส่วนใหญ่เป็นงานในกลุ่ม **"{common_best_group}"** ซึ่งสะท้อนถึงการเตรียมความพร้อมหรือสภาพเครื่องจักรที่สมบูรณ์ในจังหวะดังกล่าว
    * **🔍 ข้อเสนอแนะ:** ควรนำพารามิเตอร์การเดินงานของออเดอร์เหล่านี้มาเป็นมาตรฐาน (Best Practice) สำหรับออเดอร์ในอนาคตเพื่อรักษามาตรฐานความเร็วนี้ไว้
    """)

    # --- Data Table Block ---
    display_top_10 = top_10_gain[[
        "Speed Plan", "Actual Speed", "Diff เวลา",
        "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"
    ]].copy()
    
    # Format to integer
    for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
        display_top_10[c] = display_top_10[c].round(0).astype(int)
    
    st.dataframe(display_top_10, use_container_width=True, hide_index=True)
else:
    st.info("ไม่มีข้อมูลออเดอร์ไม่จอดเครื่องในช่วงเวลาที่เลือก")

st.divider()

# ======================================
# Charts Row 2 (Bar & Pie)
# ======================================
col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    st.markdown("#### 📦 สัดส่วนลักษณะ Order ความยาวแยกตามเครื่องจักร")
    if "เครื่องจักร" in filtered_df.columns and "ลักษณะ Order ความยาว" in filtered_df.columns:
        bar_df = filtered_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="Order Count")
        bar_df["Percent"] = bar_df.groupby("เครื่องจักร")["Order Count"].transform(lambda x: (x / x.sum() * 100).round(1))
        
        fig_bar = px.bar(
            bar_df, 
            x="Percent", 
            y="เครื่องจักร", 
            color="ลักษณะ Order ความยาว", 
            orientation="h",
            text=bar_df.apply(lambda row: f"{row['Order Count']} ({row['Percent']}%)", axis=1),
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig_bar.update_layout(
            barmode="stack", 
            xaxis=dict(title="สัดส่วนเปอร์เซ็นต์ (%)", range=[0, 105]),
            yaxis=dict(title=None),
            height=400, 
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col_ch2:
    st.markdown("#### 🛑 วิเคราะห์ลักษณะการหยุดเครื่อง (Machine Stop)")
    if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
        stop_sum = filtered_df.groupby("ลักษณะ เวลาหยุดเครื่อง", as_index=False).size().rename(columns={"size": "จำนวนครั้ง"})
        fig_pie = px.pie(stop_sum, names="ลักษณะ เวลาหยุดเครื่อง", values="จำนวนครั้ง", hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_pie.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5), template="plotly_white")
        st.plotly_chart(fig_pie, use_container_width=True)

# ======================================
# Detail Table
# ======================================
st.markdown("---")
st.subheader("📋 รายละเอียดรายการ Order (Data Logs)")

full_cols_list = [
    "วันที่", "เครื่องจักร", "กะ", 
    "ลำดับที่", "PDR", "Flute", 
    "M5", "M4", "M3", "M2", "M1", 
    "หน้ากว้าง (W) PLAN", "ความยาว (L) PLAN", "T", 
    "ความยาวเมตร PLAN", "ความยาวเมตร MC", 
    "Speed Plan", "Actual Speed", "Speed เทียบแผน", 
    "เวลา Plan", "เวลา Actual", "Diff เวลา", 
    "เวลาหยุดเครื่องจากผลิต", "เวลาหยุดข้อมูลเครื่อง", 
    "Checked-1", "Checked-2", 
    "Start Time", "Stop Time", 
    "ลักษณะ Order PLAN", "ลักษณะ Order MC", 
    "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", 
    "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"
]

existing_cols = [col for col in full_cols_list if col in filtered_df.columns]

if existing_cols:
    st.dataframe(
        filtered_df[existing_cols].sort_values("วันที่", ascending=False),
        use_container_width=True,
        height=520
    )
