import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import quote

# ======================================
# Page Config
# ======================================
st.set_page_config(
    page_title="Speed Performance Dashboard",
    page_icon="📈",
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
    st.warning("ไม่พบข้อมูลใน Google Sheet กรุณาตรวจสอบการเชื่อมต่อ")
    st.stop()

# ======================================
# Clean Data
# ======================================
df.columns = df.columns.str.strip()

# Convert Date
df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors="coerce")
if df["วันที่"].isna().all():
    df["วันที่"] = pd.to_datetime(df["วันที่"], errors="coerce")

# Convert Numeric
numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง", "Diff เวลา"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Convert Text
text_cols = ["เครื่องจักร", "กะ", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", "Checked-2", "Speed เทียบแผน"]
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'NaN', 'None', '0.0', '0'], '')

# ======================================
# Sidebar Filters
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
        options = sorted([opt for opt in df[col].unique() if opt != ""])
        return st.sidebar.multiselect(label, options)
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
# KPI CALCULATION
# ======================================
# 1. NON-STOP
ns_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง")
non_stop_order = len(filtered_df[ns_mask])
raw_ns_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง", "Diff เวลา"].sum()

# 2. STOP ORDERS
so_mask = (filtered_df["Checked-2"].str.upper() == "YES") & (filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง")
stop_orders_count = len(filtered_df[so_mask])
raw_stop_min = filtered_df.loc[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "จอดเครื่อง", ["Diff เวลา", "เวลาหยุดข้อมูลเครื่อง"]].sum().sum()

# 3. OVERALL
overall_speed_time = int(round(raw_ns_min + raw_stop_min))

# ======================================
# TABS LAYOUT
# ======================================
tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "🚩 Loss Analysis", "📋 Order Logs"])

# --------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------
with tab1:
    st.markdown("#### 🚀 Speed Performance Summary")
    
    def kpi_card(title, bg, order, time):
        return f"""
        <div style="background:{bg}; padding:20px; border-radius:15px; color:#fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">
            <h4 style="text-align:center; margin:0 0 15px 0; font-size:16px; font-weight:800; text-transform:uppercase;">{title}</h4>
            <div style="display:flex; gap:10px; justify-content:space-between;">
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Order</div>
                    <div style="font-size:22px; font-weight:800;">{order:,}</div>
                </div>
                <div style="background:rgba(255,255,255,0.2); padding:10px; border-radius:12px; flex:1; text-align:center;">
                    <div style="font-size:11px; opacity:0.85;">Time Min</div>
                    <div style="font-size:22px; font-weight:800;">{time:+,}</div>
                </div>
            </div>
        </div>
        """
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(kpi_card("NON-STOP", "#8e44ad", non_stop_order, int(round(raw_ns_min))), unsafe_allow_html=True)
    with c2: st.markdown(kpi_card("STOP ORDERS", "#d35400", stop_orders_count, int(round(raw_stop_min))), unsafe_allow_html=True)
    with c3:
        color = "#27ae60" if overall_speed_time >= 0 else "#c0392b"
        st.markdown(kpi_card("OVERALL SPEED", color, non_stop_order + stop_orders_count, overall_speed_time), unsafe_allow_html=True)

    st.markdown("---")
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.markdown("##### 📈 แนวโน้ม OVERALL SPEED (รายสัปดาห์ ISO)")
        trend_df = filtered_df.copy()
        trend_df['Val'] = trend_df.apply(lambda r: r['Diff เวลา'] if r['ลักษณะ เวลาหยุดเครื่อง'] == "ไม่จอดเครื่อง" else r['Diff เวลา'] + r['เวลาหยุดข้อมูลเครื่อง'], axis=1)
        trend_df['ISO_Week'] = trend_df['วันที่'].dt.isocalendar().week
        res_w = trend_df.groupby('ISO_Week')['Val'].sum().reset_index()
        res_w['Label'] = res_w['ISO_Week'].apply(lambda x: f"WEEK {x}")
        
        fig_w = go.Figure(go.Bar(x=res_w['Label'], y=res_w['Val'], marker_color=['#2ecc71' if v >= 0 else '#e74c3c' for v in res_w['Val']], text=res_w['Val'].round(0).astype(int), textposition='outside'))
        fig_w.update_layout(height=350, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_w, use_container_width=True)
    
    with col_t2:
        st.markdown("##### 📊 สัดส่วน Speed เทียบแผน")
        if "Speed เทียบแผน" in filtered_df.columns:
            status_df = filtered_df["Speed เทียบแผน"].value_counts().reset_index()
            fig_s = px.pie(status_df, names="Speed เทียบแผน", values="count", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_s.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            fig_s.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_s, use_container_width=True)

# --------------------------------------
# TAB 2: LOSS ANALYSIS
# --------------------------------------
with tab2:
    st.markdown("#### 🚩 วิเคราะห์ความสูญเสียสปีด (Loss Insights)")
    
    ns_loss_df = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] == "ไม่จอดเครื่อง"].copy()
    
    if not ns_loss_df.empty:
        # 1. Executive Insights
        top_10 = ns_loss_df.sort_values(by="Diff เวลา", ascending=True).head(10)
        total_lost = abs(top_10["Diff เวลา"].sum())
        
        # ค้นหาปัญหาที่พบบ่อยสุด
        prob_stats = top_10[top_10["กรุ๊ปปัญหา"] != ""]["กรุ๊ปปัญหา"].value_counts()
        main_prob = prob_stats.idxmax() if not prob_stats.empty else "ไม่ระบุ"
        
        st.error(f"""
        **💡 Executive Insights (สรุปข้อมูล 10 อันดับที่ช้าที่สุด)**
        * **⚠️ วิกฤตเวลาสูญเสีย:** เฉพาะ 10 รายการนี้เสียเวลาสะสมรวม **{total_lost:,.0f} นาที** จากสปีดที่ตกต่ำกว่าแผน
        * **🏭 สาเหตุหลักที่ต้องแก้ไข:** ปัญหาในกลุ่ม **"{main_prob}"** พบมากที่สุด ซึ่งส่งผลกระทบต่อความต่อเนื่องในการรันเครื่อง
        * **🔍 ข้อแนะนำ:** ควรตรวจสอบบันทึกรายละเอียดในตารางด้านล่าง เพื่อหาวิธีแก้ไขเชิงเทคนิคร่วมกับทีมที่เกี่ยวข้อง
        """)
        
        # 2. Pareto Chart สำหรับปัญหา
        st.markdown("##### 📉 วิเคราะห์กรุ๊ปปัญหา (Top Problems)")
        all_probs = ns_loss_df[ns_loss_df["Diff เวลา"] < 0].groupby("กรุ๊ปปัญหา")["Diff เวลา"].sum().abs().reset_index().sort_values("Diff เวลา", ascending=False)
        if not all_probs.empty:
            fig_p = px.bar(all_probs.head(5), x="Diff เวลา", y="กรุ๊ปปัญหา", orientation='h', text_auto='.0f', title="5 อันดับกรุ๊ปปัญหาที่ทำให้เสียเวลามากที่สุด (นาที)")
            fig_p.update_layout(height=300, template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_p, use_container_width=True)

        # 3. Top 10 Table
        st.markdown("##### 📋 รายการออเดอร์ที่ช้ากว่าแผนมากที่สุด 10 อันดับ")
        cols = ["Speed Plan", "Actual Speed", "Diff เวลา", "ลักษณะ Order ความยาว", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
        display_top = top_10[cols].copy()
        for c in ["Speed Plan", "Actual Speed", "Diff เวลา"]:
            display_top[c] = display_top[c].round(0).astype(int)
        st.dataframe(display_top, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบข้อมูลความล่าช้าในช่วงเวลานี้")

# --------------------------------------
# TAB 3: DATA LOGS
# --------------------------------------
with tab3:
    st.markdown("#### 📋 รายละเอียดออเดอร์และสัดส่วนงาน")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown("##### 🏭 สัดส่วนออเดอร์ตามเครื่องจักร")
        if "เครื่องจักร" in filtered_df.columns:
            bar_m = filtered_df.groupby(["เครื่องจักร", "ลักษณะ Order ความยาว"]).size().reset_index(name="Count")
            fig_m = px.bar(bar_m, x="Count", y="เครื่องจักร", color="ลักษณะ Order ความยาว", orientation="h", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_m.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_m, use_container_width=True)
    with col_l2:
        st.markdown("##### 🛑 สัดส่วนลักษณะการหยุดเครื่อง")
        if "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
            pie_stop = filtered_df[filtered_df["ลักษณะ เวลาหยุดเครื่อง"] != ""].groupby("ลักษณะ เวลาหยุดเครื่อง").size().reset_index(name="Count")
            fig_stop = px.pie(pie_stop, names="ลักษณะ เวลาหยุดเครื่อง", values="Count", hole=0.5)
            fig_stop.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_stop, use_container_width=True)

    st.markdown("---")
    st.subheader("Data Logs")
    logs_cols = ["วันที่", "เครื่องจักร", "กะ", "PDR", "Speed Plan", "Actual Speed", "Diff เวลา", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด"]
    st.dataframe(filtered_df[[c for c in logs_cols if c in filtered_df.columns]].sort_values("วันที่", ascending=False), use_container_width=True, height=500)
