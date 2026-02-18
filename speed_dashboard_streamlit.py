import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from urllib.parse import quote

# ======================================
# 1. Page Config & CSS Styling
# ======================================
st.set_page_config(
    page_title="Machine Speed Performance",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ======================================
# 2. Google Sheet Config & Data Loading
# ======================================
SHEET_ID = "1Dd1PkTf2gW8tGSXVlr6WXgA974wcvySZTnVgv2G-7QU"
SHEET_NAME = "DATA-SPEED"

# เปลี่ยนชื่อฟังก์ชันเพื่อบังคับ Clear Cache (Force Reload)
@st.cache_data(ttl=300)
def load_data_v2():
    # Construct URL for Google Sheet CSV export
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    )
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        return pd.DataFrame()

    # --- Data Cleaning Steps ---
    
    # 1. Clean Column Names (Remove leading/trailing spaces)
    df.columns = df.columns.str.strip()
    
    # 2. Convert Date 'วันที่' (Format: 27/10/25)
    try:
        df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors='coerce')
    except:
        df["วันที่"] = pd.to_datetime(df["วันที่"], errors='coerce')
        
    # 3. Convert Numeric Columns based on your FULL LIST
    # ใส่รายชื่อคอลัมน์ที่เป็นตัวเลขทั้งหมดตามที่คุณให้มา
    numeric_targets = [
        "ลำดับที่", "M5", "M4", "M3", "M2", "M1", 
        "หน้ากว้าง (W) PLAN", "ความยาว (L) PLAN", "T", 
        "ความยาวเมตร PLAN", "ความยาวเมตร MC", 
        "Speed Plan", "Actual Speed", 
        "เวลา Plan", "เวลา Actual", "Diff เวลา", 
        "เวลาหยุดเครื่องจากผลิต", "เวลาหยุดข้อมูลเครื่อง"
    ]
    
    for col in numeric_targets:
        if col in df.columns:
            # แปลงเป็นตัวเลข ถ้ามี text ปนให้เป็น 0 (coerce -> NaN -> 0)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 4. Fill Missing Strings for ALL Object Columns
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 5. Handle Start/Stop Time specifically if needed for calculation
    if "Start Time" in df.columns:
        df["Start Time"] = pd.to_datetime(df["Start Time"], format="%d/%m/%Y %H:%M", errors='coerce')
    if "Stop Time" in df.columns:
        df["Stop Time"] = pd.to_datetime(df["Stop Time"], format="%d/%m/%Y %H:%M", errors='coerce')

    return df

# Load Data
df = load_data_v2()

if df.empty:
    st.warning("ไม่สามารถดึงข้อมูลได้ กรุณาตรวจสอบ Google Sheet ID หรือ Permission")
    st.stop()

# ======================================
# 3. Sidebar Filters
# ======================================
st.sidebar.title("⚙️ Configuration")

# ปุ่ม Clear Cache เพื่อแก้ปัญหาข้อมูลไม่เปลี่ยน
if st.sidebar.button("🔄 Reload Data (Clear Cache)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# Date Filter Logic
if df["วันที่"].notna().any():
    min_date = df["วันที่"].min()
    max_date = df["วันที่"].max()
    default_start = max_date - pd.Timedelta(days=7) if pd.notnull(max_date) else datetime.now()
else:
    min_date = datetime.now()
    max_date = datetime.now()
    default_start = datetime.now()

date_range = st.sidebar.date_input(
    "📅 Select Date Range",
    value=[default_start, max_date],
    min_value=min_date,
    max_value=max_date
)

# Helper for Multiselect
def create_filter(label, col_name):
    if col_name in df.columns:
        options = sorted(df[col_name].unique())
        selected = st.sidebar.multiselect(label, options)
        return selected if selected else options
    return []

# Create Filters
selected_machines = create_filter("🏭 เครื่องจักร (Machine)", "เครื่องจักร")
selected_shifts = create_filter("⏱ กะ (Shift)", "กะ")
selected_lengths = create_filter("📦 ลักษณะ Order (Length)", "ลักษณะ Order ความยาว")

# Filter Logic
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (
        (df["วันที่"] >= pd.to_datetime(start_date)) & 
        (df["วันที่"] <= pd.to_datetime(end_date))
    )
    if "เครื่องจักร" in df.columns:
        mask &= df["เครื่องจักร"].isin(selected_machines)
    if "กะ" in df.columns:
        mask &= df["กะ"].isin(selected_shifts)
    if "ลักษณะ Order ความยาว" in df.columns:
        mask &= df["ลักษณะ Order ความยาว"].isin(selected_lengths)
        
    filtered_df = df.loc[mask]
else:
    filtered_df = df.copy()

# ======================================
# 4. Main Dashboard Area
# ======================================
st.title("🚀 Speed Performance Dashboard")
st.caption(f"Data Source: Google Sheets | Records: {len(filtered_df):,}")

tab1, tab2 = st.tabs(["📊 Executive Summary", "📋 Data Explorer"])

with tab1:
    # --- KPI SECTION ---
    st.subheader("Key Performance Indicators")
    
    total_orders = len(filtered_df)
    
    avg_plan_speed = 0
    avg_actual_speed = 0
    if "Speed Plan" in filtered_df.columns:
        # Filter out 0 for mean calculation to be accurate
        avg_plan_speed = filtered_df[filtered_df["Speed Plan"] > 0]["Speed Plan"].mean()
    if "Actual Speed" in filtered_df.columns:
        avg_actual_speed = filtered_df[filtered_df["Actual Speed"] > 0]["Actual Speed"].mean()
    
    # Handle NaN
    if pd.isna(avg_plan_speed): avg_plan_speed = 0
    if pd.isna(avg_actual_speed): avg_actual_speed = 0
    
    # Sums
    total_run_time_min = filtered_df["เวลา Actual"].sum() if "เวลา Actual" in filtered_df.columns else 0
    total_plan_time_min = filtered_df["เวลา Plan"].sum() if "เวลา Plan" in filtered_df.columns else 0
    total_stop_time_min = filtered_df["เวลาหยุดข้อมูลเครื่อง"].sum() if "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns else 0
    
    speed_diff = avg_actual_speed - avg_plan_speed
    time_diff = total_run_time_min - total_plan_time_min

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Total Orders", f"{total_orders:,}", "Count")
    with kpi2:
        st.metric("Avg Actual Speed", f"{avg_actual_speed:,.1f}", f"{speed_diff:+.1f} vs Plan")
    with kpi3:
        hours = total_run_time_min / 60
        st.metric("Production Time", f"{hours:,.1f} hrs", f"{time_diff/60:+.1f} hrs vs Plan")
    with kpi4:
        stop_hours = total_stop_time_min / 60
        st.metric("Stop Time", f"{stop_hours:,.1f} hrs", delta=None, delta_color="off")

    st.markdown("---")

    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Speed Trend: Plan vs Actual")
        if "วันที่" in filtered_df.columns and not filtered_df.empty:
            daily_speed = filtered_df.groupby("วันที่")[["Speed Plan", "Actual Speed"]].mean().reset_index()
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=daily_speed["วันที่"], y=daily_speed["Speed Plan"], 
                                        mode='lines', name='Plan Speed', line=dict(color='#bdc3c7', dash='dash')))
            fig_line.add_trace(go.Scatter(x=daily_speed["วันที่"], y=daily_speed["Actual Speed"], 
                                        mode='lines+markers', name='Actual Speed', line=dict(color='#2ecc71', width=3)))
            fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("🛑 Stop Causes Analysis")
        # Ensure column exists
        if "เวลาหยุดข้อมูลเครื่อง" in filtered_df.columns and "ลักษณะ เวลาหยุดเครื่อง" in filtered_df.columns:
            stop_data = filtered_df[filtered_df["เวลาหยุดข้อมูลเครื่อง"] > 0]
            if not stop_data.empty:
                stop_summary = stop_data.groupby("ลักษณะ เวลาหยุดเครื่อง")["เวลาหยุดข้อมูลเครื่อง"].sum().reset_index()
                fig_pie = px.donut(stop_summary, values='เวลาหยุดข้อมูลเครื่อง', names='ลักษณะ เวลาหยุดเครื่อง', 
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=0, b=20), showlegend=False)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No stop time recorded in this period.")
        else:
            st.warning("Missing columns for Stop Analysis")

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🏭 Performance by Machine")
        if "Speed เทียบแผน" in filtered_df.columns and not filtered_df.empty:
            status_by_machine = filtered_df.groupby(["เครื่องจักร", "Speed เทียบแผน"]).size().reset_index(name="Count")
            fig_bar = px.bar(status_by_machine, x="Count", y="เครื่องจักร", color="Speed เทียบแผน", 
                             orientation='h', title="Count of Speed Status by Machine",
                             color_discrete_map={"เร็วกว่าแผน": "#2ecc71", "ตามแผน": "#3498db", "ช้ากว่าแผน": "#e74c3c", "ยกเลิกเดินงาน": "#95a5a6"})
            fig_bar.update_layout(height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

    with c4:
        st.subheader("📦 Speed vs Order Length")
        if "ลักษณะ Order ความยาว" in filtered_df.columns and not filtered_df.empty:
            scatter_df = filtered_df[filtered_df["Actual Speed"] > 0]
            if not scatter_df.empty:
                # Add hover data if columns exist
                hover_data = []
                for h_col in ["PDR", "เครื่องจักร", "Start Time"]:
                    if h_col in scatter_df.columns:
                        hover_data.append(h_col)
                        
                fig_scatter = px.scatter(scatter_df, x="Actual Speed", y="เวลา Actual", color="ลักษณะ Order ความยาว",
                                       hover_data=hover_data,
                                       title="Correlation: Speed vs Operation Time")
                fig_scatter.update_layout(height=300)
                st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("📋 Detailed Data View")
    
    if filtered_df.empty:
        st.warning("⚠️ ไม่พบข้อมูลตามเงื่อนไขที่เลือก (No data found)")
    else:
        # Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv,
            file_name='filtered_speed_data.csv',
            mime='text/csv',
        )
        
        # --- Column Management using YOUR EXACT LIST ---
        # ก๊อปปี้รายชื่อคอลัมน์ที่คุณให้มาใส่ลงไปตรงนี้เป๊ะๆ
        user_defined_cols = [
            "ลำดับที่", "PDR", "Flute", "M5", "M4", "M3", "M2", "M1", 
            "หน้ากว้าง (W) PLAN", "ความยาว (L) PLAN", "T", 
            "ความยาวเมตร PLAN", "ความยาวเมตร MC", 
            "Speed Plan", "Actual Speed", "Speed เทียบแผน", 
            "เวลา Plan", "เวลา Actual", "Diff เวลา", 
            "เวลาหยุดเครื่องจากผลิต", "เวลาหยุดข้อมูลเครื่อง", 
            "Checked-1", "Checked-2", "Start Time", "Stop Time", 
            "ลักษณะ Order PLAN", "ลักษณะ Order MC", 
            "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว", 
            "กะ", "สาเหตุจาก", "กรุ๊ปปัญหา", "รายละเอียด", 
            "เครื่องจักร", "วันที่"
        ]
        
        # 1. Start with priority columns that exist in the dataframe
        default_cols = [c for c in user_defined_cols if c in filtered_df.columns]
        
        # 2. Add remaining columns (if any exist in data but not in your list)
        all_cols_in_data = filtered_df.columns.tolist()
        remaining_cols = [c for c in all_cols_in_data if c not in default_cols]
        
        # Allow user to select columns
        selected_cols = st.multiselect(
            "Select Columns to Display:",
            options=all_cols_in_data,
            default=default_cols + remaining_cols[:2]  # Show your list by default
        )
        
        if not selected_cols:
            st.info("Please select at least one column.")
        else:
            # Create a display copy AND RESET INDEX to prevent style errors
            display_df = filtered_df[selected_cols].copy().reset_index(drop=True)

            # Style function
            def highlight_status(row):
                color = ''
                if "Speed เทียบแผน" in row.index:
                    status = str(row["Speed เทียบแผน"])
                    if "ช้ากว่าแผน" in status:
                        color = 'background-color: #ffebee' # Red tint
                    elif "เร็วกว่าแผน" in status:
                        color = 'background-color: #e8f5e9' # Green tint
                return [color] * len(row)

            # Format numbers (Integer format for cleaner look)
            # เพิ่มคอลัมน์ตัวเลขให้ครบถ้วน
            format_dict = {
                "Speed Plan": "{:.0f}", "Actual Speed": "{:.0f}", 
                "เวลา Plan": "{:.0f}", "เวลา Actual": "{:.0f}",
                "Diff เวลา": "{:.0f}", "หน้ากว้าง (W) PLAN": "{:.0f}", 
                "ความยาว (L) PLAN": "{:.0f}", "ความยาวเมตร PLAN": "{:.0f}",
                "ความยาวเมตร MC": "{:.0f}", "T": "{:.0f}",
                "M1": "{:.0f}", "M2": "{:.0f}", "M3": "{:.0f}", 
                "M4": "{:.0f}", "M5": "{:.0f}"
            }
            # Only apply format if column exists in selection
            valid_format = {k: v for k, v in format_dict.items() if k in display_df.columns}

            try:
                st.dataframe(
                    display_df.style.apply(highlight_status, axis=1).format(valid_format),
                    use_container_width=True,
                    height=600
                )
            except Exception as e:
                # Robust Fallback
                st.warning(f"Note: Styling disabled due to data structure. Showing raw table.")
                st.dataframe(display_df, use_container_width=True, height=600)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Dashboard © 2026</div>", unsafe_allow_html=True)
