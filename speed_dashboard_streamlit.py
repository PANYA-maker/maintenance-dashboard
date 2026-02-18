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

@st.cache_data(ttl=300)
def load_and_clean_data():
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
    
    # 1. Clean Column Names
    df.columns = df.columns.str.strip()
    
    # 2. Convert Date 'วันที่'
    # Try multiple formats or fallback to default
    try:
        df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d/%m/%y", errors='coerce')
    except:
        df["วันที่"] = pd.to_datetime(df["วันที่"], errors='coerce')
        
    # 3. Convert Numeric Columns (Handle text like 'ยกเลิกเดินงาน')
    numeric_cols = ["Speed Plan", "Actual Speed", "เวลา Plan", "เวลา Actual", "เวลาหยุดข้อมูลเครื่อง"]
    
    for col in numeric_cols:
        if col in df.columns:
            # Force convert to numeric, turn errors (text) into NaN, then fill with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 4. Fill Missing Strings
    str_cols = ["เครื่องจักร", "กะ", "Speed เทียบแผน", "ลักษณะ เวลาหยุดเครื่อง", "ลักษณะ Order ความยาว"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)

    return df

# Load Data
df = load_and_clean_data()

if df.empty:
    st.warning("ไม่สามารถดึงข้อมูลได้ กรุณาตรวจสอบ Google Sheet ID หรือ Permission")
    st.stop()

# ======================================
# 3. Sidebar Filters
# ======================================
st.sidebar.title("⚙️ Configuration")
st.sidebar.markdown("---")

# Date Filter
min_date = df["วันที่"].min()
max_date = df["วันที่"].max()

# Default to last 7 days available data
default_start = max_date - pd.Timedelta(days=7) if pd.notnull(max_date) else datetime.now()

date_range = st.sidebar.date_input(
    "📅 Select Date Range",
    value=[default_start, max_date],
    min_value=min_date,
    max_value=max_date
)

# Helper for Multiselect with "All" option implicitly
def create_filter(label, col_name):
    options = sorted(df[col_name].unique())
    selected = st.sidebar.multiselect(label, options)
    return selected if selected else options

# Create Filters
selected_machines = create_filter("🏭 เครื่องจักร (Machine)", "เครื่องจักร")
selected_shifts = create_filter("⏱ กะ (Shift)", "กะ")
selected_lengths = create_filter("📦 ลักษณะ Order (Length)", "ลักษณะ Order ความยาว")

# Filter Logic
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (
        (df["วันที่"] >= pd.to_datetime(start_date)) & 
        (df["วันที่"] <= pd.to_datetime(end_date)) &
        (df["เครื่องจักร"].isin(selected_machines)) &
        (df["กะ"].isin(selected_shifts)) &
        (df["ลักษณะ Order ความยาว"].isin(selected_lengths))
    )
    filtered_df = df.loc[mask]
else:
    filtered_df = df.copy() # Fallback

# ======================================
# 4. Main Dashboard Area
# ======================================
st.title("🚀 Speed Performance Dashboard")
st.caption(f"Data Source: Google Sheets | Records: {len(filtered_df):,}")

tab1, tab2 = st.tabs(["📊 Executive Summary", "📋 Data Explorer"])

with tab1:
    # --- KPI SECTION ---
    st.subheader("Key Performance Indicators")
    
    # Calculate KPIs
    total_orders = len(filtered_df)
    
    # Speed (Avoid division by zero)
    avg_plan_speed = filtered_df[filtered_df["Speed Plan"] > 0]["Speed Plan"].mean()
    avg_actual_speed = filtered_df[filtered_df["Actual Speed"] > 0]["Actual Speed"].mean()
    if pd.isna(avg_plan_speed): avg_plan_speed = 0
    if pd.isna(avg_actual_speed): avg_actual_speed = 0
    
    # Time
    total_run_time_min = filtered_df["เวลา Actual"].sum()
    total_plan_time_min = filtered_df["เวลา Plan"].sum()
    total_stop_time_min = filtered_df["เวลาหยุดข้อมูลเครื่อง"].sum()
    
    # Diff Calculation
    speed_diff = avg_actual_speed - avg_plan_speed
    time_diff = total_run_time_min - total_plan_time_min

    # Create 4 Columns for Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Total Orders", f"{total_orders:,}", "Count")
    with kpi2:
        st.metric("Avg Actual Speed", f"{avg_actual_speed:,.1f}", f"{speed_diff:+.1f} vs Plan")
    with kpi3:
        # Convert min to Hours
        hours = total_run_time_min / 60
        st.metric("Production Time", f"{hours:,.1f} hrs", f"{time_diff/60:+.1f} hrs vs Plan")
    with kpi4:
        stop_hours = total_stop_time_min / 60
        st.metric("Stop Time", f"{stop_hours:,.1f} hrs", delta=None, delta_color="off")

    st.markdown("---")

    # --- CHARTS SECTION TOP ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Speed Trend: Plan vs Actual")
        # Daily Average Speed
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
        # Filter only rows with Stop Time > 0
        stop_data = filtered_df[filtered_df["เวลาหยุดข้อมูลเครื่อง"] > 0]
        stop_summary = stop_data.groupby("ลักษณะ เวลาหยุดเครื่อง")["เวลาหยุดข้อมูลเครื่อง"].sum().reset_index()
        
        if not stop_summary.empty:
            fig_pie = px.donut(stop_summary, values='เวลาหยุดข้อมูลเครื่อง', names='ลักษณะ เวลาหยุดเครื่อง', 
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=0, b=20), showlegend=False)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No stop time data for selected range.")

    # --- CHARTS SECTION BOTTOM ---
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("🏭 Performance by Machine")
        # Stacked bar chart for Speed Status
        status_by_machine = filtered_df.groupby(["เครื่องจักร", "Speed เทียบแผน"]).size().reset_index(name="Count")
        
        fig_bar = px.bar(status_by_machine, x="Count", y="เครื่องจักร", color="Speed เทียบแผน", 
                         orientation='h', title="Count of Speed Status by Machine",
                         color_discrete_map={"เร็วกว่าแผน": "#2ecc71", "ตามแผน": "#3498db", "ช้ากว่าแผน": "#e74c3c", "ยกเลิกเดินงาน": "#95a5a6"})
        fig_bar.update_layout(height=300)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c4:
        st.subheader("📦 Speed vs Order Length")
        # Scatter plot to see if Length affects Speed
        # Clean data for scatter (remove 0 speeds)
        scatter_df = filtered_df[filtered_df["Actual Speed"] > 0]
        
        fig_scatter = px.scatter(scatter_df, x="Actual Speed", y="เวลา Actual", color="ลักษณะ Order ความยาว",
                               hover_data=["PDR", "เครื่องจักร"],
                               title="Correlation: Speed vs Operation Time")
        fig_scatter.update_layout(height=300)
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    # --- DATA TABLE ---
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
        
        # Define desired columns
        target_cols = [
            "วันที่", "เครื่องจักร", "PDR", "Speed Plan", "Actual Speed", 
            "Speed เทียบแผน", "เวลา Plan", "เวลา Actual", "ลักษณะ เวลาหยุดเครื่อง"
        ]
        
        # Filter only columns that actually exist in the dataframe to prevent errors
        cols_to_show = [c for c in target_cols if c in filtered_df.columns]

        if not cols_to_show:
            st.error("ไม่พบคอลัมน์ที่ต้องการแสดงผล")
            st.write("Columns found:", filtered_df.columns.tolist())
        else:
            # Create a display copy
            display_df = filtered_df[cols_to_show].copy()

            # Style function: Highlight rows based on 'Speed เทียบแผน'
            def highlight_status(row):
                color = ''
                # Check if column exists in this row/index before accessing
                if "Speed เทียบแผน" in row.index:
                    status = str(row["Speed เทียบแผน"])
                    if status == "ช้ากว่าแผน":
                        color = 'background-color: #ffebee' # Red tint
                    elif status == "เร็วกว่าแผน":
                        color = 'background-color: #e8f5e9' # Green tint
                return [color] * len(row)

            # Define format dict only for existing columns
            format_dict = {
                "Speed Plan": "{:.0f}", "Actual Speed": "{:.0f}", 
                "เวลา Plan": "{:.0f}", "เวลา Actual": "{:.0f}"
            }
            valid_format = {k: v for k, v in format_dict.items() if k in display_df.columns}

            try:
                # Display Styled DataFrame
                st.dataframe(
                    display_df.style.apply(highlight_status, axis=1)
                    .format(valid_format),
                    use_container_width=True,
                    height=600
                )
            except Exception as e:
                # Fallback if styling fails
                st.warning(f"Styling failed, showing plain table. Error: {e}")
                st.dataframe(display_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Speed Analytics Dashboard © 2026</div>", unsafe_allow_html=True)
