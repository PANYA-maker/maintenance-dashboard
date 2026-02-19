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

# ลบช่องว่างในข้อความ และจัดการค่าว่าง (nan) ให้เป็นค่าว่างจริง
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].fillna("").astype(str).str.strip()
    df[col] = df[col].replace(['nan', 'NaN', 'None'], '')

# ======================================
# Sidebar Filters
# ======================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

if df["วันที่"].notna().any():
    max_date = df["วันที่"].max()
    min_7days = max_date - pd.Timedelta(days=6)
else:
    max_date = pd.Timestamp.today()
    min_7days = max_date

date_range = st.sidebar.date_input("📅 เลือกช่วงวันที่", [min_7days, max_date])

def multi_filter(label, col):
    if col in df.columns:
        return st.sidebar.multiselect(label, sorted([o for o in df[col].unique() if o != ""]))
    return []

machines = multi_filter("🏭 เครื่องจักร", "เครื่องจักร")
shifts = multi_filter("⏱ กะ", "กะ")
speed_status = multi_filter("📊 Speed เทียบแผน", "Speed เทียบแผน")
stop_types = multi_filter("🛑 ลักษณะเวลาหยุดเครื่อง", "ลักษณะ เวลาหยุดเครื่อง")
order_lengths = multi_filter("📦 ลักษณะ Order ความยาว", "ลักษณะ Order ความยาว")

# Apply Filters
if len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = df[(df["วันที่"] >= start_dt) & (df["วันที่"] <= end_dt)].copy()
else:
    filtered_df = df.copy()

if machines: filtered_df = filtered_df[filtered_df["เครื่องจักร"].isin(machines)]
if shifts: filtered_df = filtered_df[filtered_df["กะ"].isin(shifts)]
if speed_status: filtered_df = filtered_df[filtered_df["Speed เทียบแผน"].isin(speed_status)]
if stop_types: filtered_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"].isin(stop_types)]
if order_lengths: filtered_df = filtered_df[filtered_df["ลักษณะ Order ความยาว"].isin(order_lengths)]

# ======================================
# KPI CALCULATION
# ======================================
# 1. NON-STOP
ns_cond = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
non_stop_order = len(filtered_df[ns_cond])
raw_ns_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# 2. STOP ORDERS
stop_cond = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
stop_orders_count = len(filtered_df[stop_cond])
raw_stop_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# 3. OVERALL
overall_speed_time = int(round(raw_ns_min + raw_stop_min))

# ======================================
# TABBED LAYOUT (หัวใจสำคัญของการแบ่งหน้า)
# ======================================
tab_summary, tab_insights, tab_details = st.tabs([
    "📈 ภาพรวมประสิทธิภาพ (Overview)", 
    "🚩 วิเคราะห์ความสูญเสีย (Loss Insights)", 
    "📋 รายละเอียดข้อมูล (Data Logs)"
])

# --------------------------------------
# TAB 1: Dashboard Overview
# --------------------------------------
with tab_summary:
    st.markdown("### 📊 Performance KPI")
    
    def kpi_card_compact(title, bg_color, order_val, minute_val):
        return f"""
        <div style="background:{bg_color}; padding:20px 15px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">
            <h4 style="text-align:center; margin:0 0 15px 0; font-size:16px; font-weight: 800; text-transform: uppercase;">{title}</h4>
            <div style="display:flex; gap:10px; justify-content:space-between;">
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Order</div>
                    <div style="font-size:22px; font-weight:800;">{order_val:,}</div>
                </div>
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Time Min</div>
                    <div style="font-size:22px; font-weight:800;">{minute_val:+,}</div>
                </div>
            </div>
        </div>
        """
    
    col_ns, col_so, col_ov = st.columns(3)
    with col_ns: st.markdown(kpi_card_compact("NON-STOP", "#8e44ad", non_stop_order, int(round(raw_ns_min))), unsafe_allow_html=True)
    with col_so: st.markdown(kpi_card_compact("STOP ORDERS", "#d35400", stop_orders_count, int(round(raw_stop_min))), unsafe_allow_html=True)
    with col_ov: 
        ov_color = "#27ae60" if overall_speed_time >= 0 else "#c0392b"
        st.markdown(kpi_card_compact("OVERALL SPEED", ov_color, non_stop_order + stop_orders_count, overall_speed_time), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📉 แนวโน้มประสิทธิภาพเวลา")
    
    trend_data = filtered_df.copy()
    trend_data['Val'] = trend_data.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
    
    freq_option = st.selectbox("เลือกความถี่:", options=["รายวัน", "รายสัปดาห์", "รายเดือน"])
    
    if freq_option == "รายสัปดาห์":
        trend_data['ISO_Week'] = trend_data['วันที่'].dt.isocalendar().week
        res = trend_data.groupby('ISO_Week')['Val'].sum().reset_index()
        res['Label'] = res['ISO_Week'].apply(lambda x: f"WEEK {x}")
    else:
        m = {"รายวัน": "D", "รายเดือน": "MS"}
        res = trend_data.set_index('วันที่')['Val'].resample(m[freq_option]).sum().reset_index()
        res['Label'] = res['วันที่'].dt.strftime('%d/%m/%Y' if freq_option == "รายวัน" else '%m/%Y')

    fig_trend = go.Figure(go.Bar(x=res['Label'], y=res['Val'], marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res['Val']], text=res['Val'].round(0).astype(int), textposition='outside'))
    fig_trend.update_layout(height=400, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------
# TAB 2: Loss Analysis & Insights
# --------------------------------------
with tab_insights:
    st.markdown("### 🚩 เจาะลึกความสูญเสียสปีด (Loss Analysis)")
    
    ns_loss_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()
    
    if not ns_loss_df.empty:
        top_10_worst = ns_loss_df.sort_values(by="Diff เวลา", ascending=True).head(10)
        
        # Insights Block
        total_loss = abs(top_10_worst["Diff เวลา"].sum())
        main_prob = top_10_worst[top_10_worst["กรุ๊ปปัญหา"] != ""]["กรุ๊ปปัญหา"].value_counts().idxmax() if not top_10_worst[top_10_worst["กรุ๊ปปัญหา"] == ""].empty else "ไม่ระบุ"
        
        st.error(f"""
        **💡 Executive Insights (10 อันดับที่ช้าที่สุด)**
        * **⚠️ วิกฤตเวลาสูญเสีย:** พบความล่าช้ารวมสะสม **{total_loss:,.0f} นาที** จากเพียง 10 รายการนี้ (ขณะเครื่องจักรยังรันอยู่)
        * **🏭 สาเหตุหลักที่พบบ่อย:** ปัญหาในกลุ่ม **"{main_prob}"** เป็นตัวการหลักที่ทำให้สปีดต่ำกว่าเป้าหมาย
        * **🔍 ข้อเสนอแนะ:** ฝ่ายบริหารควรเร่งตรวจสอบช่อง "รายละเอียด" เพื่อวิเคราะห์หาสาเหตุเชิงลึกร่วมกับทีมเทคนิค
        """)
        
        # Top 10 Table
        target_cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top_10 = top_10_worst[target_cols].copy()
        for col in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            display_top_10[col] = display_top_10[col].round(0).astype(int)
        
        st.dataframe(display_top_10, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบออเดอร์ประเภท 'ไม่จอดเครื่อง' ที่ช้ากว่าแผนในช่วงเวลานี้")

# --------------------------------------
# TAB 3: Data Logs & Charts
# --------------------------------------
with tab_details:
    st.markdown("### 📊 การวิเคราะห์ข้อมูลรายออเดอร์")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📦 สัดส่วนออเดอร์แยกตามเครื่องจักร")
        if "เครื่องจักร" in filtered_df.columns:
            bar_df = filtered_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="C")
            fig_b = px.bar(bar_df, x="C", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_b, use_container_width=True)
    with c2:
        st.markdown("#### 🛑 สัดส่วนการหยุดเครื่อง")
        if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
            pie_df = filtered_df.groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="C")
            fig_p = px.pie(pie_df, names="ลักษณะ เวลาหยุดเครื่อง", values="C", hole=0.5)
            st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 รายละเอียดออเดอร์ทั้งหมด (Logs)")
    logs_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    st.dataframe(filtered_df[[c for c in logs_cols if c in filtered_df.columns]].sort_values("วันที่", ascending=False), use_container_width=True, height=500)
