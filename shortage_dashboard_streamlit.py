# =====================================
# Shortage Dashboard : DATA CHECK
# Executive Version (UI + Chart + Reset)
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Shortage Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------- Executive CSS (STEP 1) ----------------
st.markdown("""
<style>
.kpi-card {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
}
.kpi-title {
    font-size: 14px;
    color: #666;
}
.kpi-value {
    font-size: 38px;
    font-weight: bold;
}
.green { color: #2e7d32; }
.red { color: #c62828; }
.blue { color: #1565c0; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheet Config ----------------
SHEET_ID = "1gW0lw9XS0JYST-P-ZrXoFq0k4n2ZlXu9hOf3A--JV9U"
GID = "1799697899"

csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# ---------------- Load Data ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(csv_url)

    # ป้องกัน space แฝงในชื่อคอลัมน์
    df.columns = df.columns.str.strip()

    # แปลงวันที่ (ข้อมูลไทย)
    df['วันที่'] = pd.to_datetime(
        df['วันที่'],
        dayfirst=True,
        errors='coerce'
    )
    return df

df = load_data()

# ---------------- Sidebar Filters + RESET (STEP 3) ----------------
st.sidebar.header("🔎 ตัวกรองข้อมูล")

if st.sidebar.button("🔄 RESET FILTER"):
    st.session_state.clear()
    st.experimental_rerun()

date_range = st.sidebar.date_input(
    "เลือกช่วงวันที่",
    [df['วันที่'].min(), df['วันที่'].max()]
)

mc_filter = st.sidebar.multiselect(
    "MC", sorted(df['MC'].dropna().unique())
)

shift_filter = st.sidebar.multiselect(
    "กะ", sorted(df['กะ'].dropna().unique())
)

status_filter = st.sidebar.multiselect(
    "สถานะผลิต", sorted(df['สถานะผลิต'].dropna().unique())
)

customer_filter = st.sidebar.multiselect(
    "ชื่อลูกค้า", sorted(df['ชื่อลูกค้า'].dropna().unique())
)

# ---------------- Apply Filters ----------------
fdf = df[
    (df['วันที่'] >= pd.to_datetime(date_range[0])) &
    (df['วันที่'] <= pd.to_datetime(date_range[1]))
]

if mc_filter:
    fdf = fdf[fdf['MC'].isin(mc_filter)]

if shift_filter:
    fdf = fdf[fdf['กะ'].isin(shift_filter)]

if status_filter:
    fdf = fdf[fdf['สถานะผลิต'].isin(status_filter)]

if customer_filter:
    fdf = fdf[fdf['ชื่อลูกค้า'].isin(customer_filter)]

# ---------------- KPI Cards (STEP 1) ----------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ORDER TOTAL</div>
        <div class="kpi-value blue">{len(fdf):,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ครบจำนวน</div>
        <div class="kpi-value green">
            {(fdf['สถานะผลิต']=='ครบจำนวน').sum():,}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ขาดจำนวน</div>
        <div class="kpi-value red">
            {(fdf['สถานะผลิต']=='ขาดจำนวน').sum():,}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---------------- Charts (STEP 2) ----------------
left, right = st.columns([2, 1])

# ---- TOP 10 สาเหตุขาดจำนวน ----
with left:
    top10 = (
        fdf[fdf['สถานะผลิต'] == 'ขาดจำนวน']
        .groupby('Detail')
        .size()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name='จำนวน')
    )

    fig_top10 = px.bar(
        top10,
        x='จำนวน',
        y='Detail',
        orientation='h',
        title="TOP 10 สาเหตุขาดจำนวน",
        color='จำนวน',
        color_continuous_scale='Reds'
    )

    st.plotly_chart(fig_top10, use_container_width=True)

# ---- Donut สถานะผลิต ----
with right:
    status_df = (
        fdf['สถานะผลิต']
        .value_counts()
        .reset_index()
    )
    status_df.columns = ['สถานะ', 'จำนวน']

    fig_status = px.pie(
        status_df,
        names='สถานะ',
        values='จำนวน',
        hole=0.6,
        title="สัดส่วนสถานะผลิต",
        color='สถานะ',
        color_discrete_map={
            'ครบจำนวน': '#2e7d32',
            'ขาดจำนวน': '#c62828'
        }
    )

    st.plotly_chart(fig_status, use_container_width=True)

# ---------------- Data Table ----------------
st.divider()
st.subheader("📋 รายละเอียด Order (DATA CHECK)")

st.dataframe(
    fdf.sort_values('วันที่', ascending=False),
    use_container_width=True,
    height=520
)

st.caption("Shortage Dashboard | DATA CHECK (Executive Version)")
