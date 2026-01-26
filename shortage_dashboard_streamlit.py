# =====================================
# Shortage Dashboard : DATA CHECK
# FINAL PROD VERSION
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


# ---------------- Google Sheet Config ----------------
SHEET_ID = "1gW0lw9XS0JYST-P-ZrXoFq0k4n2ZlXu9hOf3A--JV9U"
GID = "1799697899"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"


# ---------------- Load Data (Auto Refresh) ----------------
@st.cache_data(ttl=300)  # 🔄 refresh ทุก 5 นาที
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()

    df["วันที่"] = pd.to_datetime(
        df["วันที่"],
        dayfirst=True,
        errors="coerce"
    )
    return df


df = load_data()


# =========================
# Sidebar
# =========================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

# ----- Manual Refresh -----
if st.sidebar.button("🔄 โหลดข้อมูลล่าสุดจาก Google Sheet"):
    st.cache_data.clear()
    st.rerun()

# ----- Default Date : Last 7 Days -----
max_date = df["วันที่"].max()
default_start = max_date - pd.Timedelta(days=7)

date_range = st.sidebar.date_input(
    "เลือกช่วงวันที่",
    value=[default_start.date(), max_date.date()],
    min_value=df["วันที่"].min().date(),
    max_value=max_date.date()
)

mc_filter = st.sidebar.multiselect(
    "MC", sorted(df["MC"].dropna().unique())
)

shift_filter = st.sidebar.multiselect(
    "กะ", sorted(df["กะ"].dropna().unique())
)

status_filter = st.sidebar.multiselect(
    "สถานะผลิต", sorted(df["สถานะผลิต"].dropna().unique())
)

customer_filter = st.sidebar.multiselect(
    "ชื่อลูกค้า", sorted(df["ชื่อลูกค้า"].dropna().unique())
)

st.sidebar.subheader("📊 แนวโน้มตามช่วงเวลา")
period = st.sidebar.selectbox(
    "เลือกช่วงเวลา",
    ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"]
)


# =========================
# Apply Filters
# =========================
fdf = df[
    (df["วันที่"] >= pd.to_datetime(date_range[0])) &
    (df["วันที่"] <= pd.to_datetime(date_range[1]))
]

if mc_filter:
    fdf = fdf[fdf["MC"].isin(mc_filter)]

if shift_filter:
    fdf = fdf[fdf["กะ"].isin(shift_filter)]

if status_filter:
    fdf = fdf[fdf["สถานะผลิต"].isin(status_filter)]

if customer_filter:
    fdf = fdf[fdf["ชื่อลูกค้า"].isin(customer_filter)]


# =========================
# KPI
# =========================
k1, k2, k3 = st.columns(3)

order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()

k1.metric("ORDER TOTAL", f"{order_total:,}")
k2.metric("ครบจำนวน", f"{complete_qty:,}")
k3.metric("ขาดจำนวน", f"{short_qty:,}")

st.divider()


# =========================
# TOP 10 + Donut
# =========================
left, right = st.columns([2, 1])

# ----- TOP 10 Shortage -----
with left:
    top10 = (
        fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]
        .groupby("Detail")
        .size()
        .sort_values()
        .tail(10)
        .reset_index(name="จำนวน")
    )

    if not top10.empty:
        top10["เปอร์เซ็นต์"] = (top10["จำนวน"] / order_total * 100).round(1)
        top10["label"] = top10["จำนวน"].astype(str) + " (" + top10["เปอร์เซ็นต์"].astype(str) + "%)"

        fig_top10 = px.bar(
            top10,
            x="จำนวน",
            y="Detail",
            orientation="h",
            title="TOP 10 สาเหตุขาดจำนวน (% เทียบ ORDER TOTAL)",
            color="จำนวน",
            color_continuous_scale="Reds",
            text="label"
        )

        fig_top10.update_traces(
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(
                color="blue",
                size=13,
                family="Arial Black"
            )
        )

        fig_top10.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            xaxis_title="จำนวน",
            uniformtext_minsize=10,
            uniformtext_mode="show"
        )

        st.plotly_chart(fig_top10, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลขาดจำนวนในช่วงที่เลือก")


# ----- Donut Status -----
with right:
    if not fdf.empty:
        status_df = fdf["สถานะผลิต"].value_counts().reset_index()
        status_df.columns = ["สถานะ", "จำนวน"]

        fig_status = px.pie(
            status_df,
            names="สถานะ",
            values="จำนวน",
            hole=0.6,
            title="สัดส่วนสถานะผลิต",
            color="สถานะ",
            color_discrete_map={
                "ครบจำนวน": "#2e7d32",
                "ขาดจำนวน": "#c62828"
            }
        )

        st.plotly_chart(fig_status, use_container_width=True)


# =========================
# STACKED BAR : Percent
# =========================
st.divider()
st.subheader("📊 เปอร์เซ็นต์ ครบจำนวน / ขาดจำนวน")

trend = fdf.copy()

if not trend.empty:
    if period == "รายวัน":
        trend["ช่วง"] = trend["วันที่"].dt.strftime("%d/%m/%Y")

    elif period == "รายสัปดาห์":
        week_start = trend["วันที่"] - pd.to_timedelta(
            (trend["วันที่"].dt.weekday + 1) % 7, unit="D"
        )
        year = week_start.dt.year
        first_sunday = pd.to_datetime(year.astype(str) + "-01-01") - pd.to_timedelta(
            (pd.to_datetime(year.astype(str) + "-01-01").dt.weekday + 1) % 7, unit="D"
        )
        week_no = ((week_start - first_sunday).dt.days // 7) + 1
        trend["ช่วง"] = "Week " + week_no.astype(str) + " / " + year.astype(str)

    elif period == "รายเดือน":
        trend["ช่วง"] = trend["วันที่"].dt.to_period("M").astype(str)

    elif period == "รายปี":
        trend["ช่วง"] = trend["วันที่"].dt.year.astype(str)

    summary = (
        trend.groupby(["ช่วง", "สถานะผลิต"])
        .size()
        .reset_index(name="จำนวน")
    )

    total = summary.groupby("ช่วง")["จำนวน"].sum().reset_index(name="รวม")
    summary = summary.merge(total, on="ช่วง")

    summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / summary["รวม"] * 100).round(1)
    summary["label"] = summary["จำนวน"].astype(str) + " (" + summary["เปอร์เซ็นต์"].astype(str) + "%)"

    summary["สถานะผลิต"] = pd.Categorical(
        summary["สถานะผลิต"],
        categories=["ครบจำนวน", "ขาดจำนวน"],
        ordered=True
    )

    fig_stack = px.bar(
        summary,
        x="ช่วง",
        y="เปอร์เซ็นต์",
        color="สถานะผลิต",
        text="label",
        barmode="stack",
        color_discrete_map={
            "ครบจำนวน": "#2e7d32",
            "ขาดจำนวน": "#c62828"
        }
    )

    fig_stack.update_layout(
        yaxis_range=[0, 100],
        yaxis_title="เปอร์เซ็นต์ (%)",
        xaxis_title="ช่วงเวลา"
    )

    fig_stack.update_traces(textposition="inside", textfont_size=13)
    st.plotly_chart(fig_stack, use_container_width=True)


# =========================
# SHORTAGE ISSUE SUMMARY
# =========================
st.divider()
st.subheader("🛠️ สรุปปัญหาสถานะซ่อม (เฉพาะงานขาดจำนวน)")

if "สถานะซ่อมสรุป" in fdf.columns:
    issue_base = fdf[
        (fdf["สถานะผลิต"] == "ขาดจำนวน") &
        (fdf["สถานะซ่อมสรุป"].notna())
    ]

    if not issue_base.empty:
        issue_summary = (
            issue_base["สถานะซ่อมสรุป"]
            .value_counts()
            .rename("จำนวน")
            .reset_index()
            .rename(columns={"index": "สถานะซ่อมสรุป"})
        )

        c1, c2 = st.columns([1, 1])

        with c1:
            st.markdown("### 📋 ตารางสรุปปัญหา")
            st.dataframe(issue_summary, use_container_width=True, height=350)

        with c2:
            fig_issue = px.pie(
                issue_summary,
                names="สถานะซ่อมสรุป",
                values="จำนวน",
                hole=0.5,
                title="สัดส่วนปัญหาสถานะซ่อม"
            )
            fig_issue.update_traces(
                textinfo="percent+label",
                textposition="inside",
                textfont_size=13
            )
            st.plotly_chart(fig_issue, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถานะซ่อมสำหรับงานขาดจำนวน")
else:
    st.warning("ไม่พบคอลัมน์ 'สถานะซ่อมสรุป'")


# =========================
# Table
# =========================
st.divider()
st.subheader("📋 รายละเอียด Order")

fdf_display = fdf.copy()
fdf_display["วันที่"] = fdf_display["วันที่"].dt.strftime("%d/%m/%Y")

display_columns = [
    "วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า",
    "M1", "M3", "M5", "ลอน",
    "ความยาวทั้งหมด(เมตร)", "ความยาว/แผ่น(มม)", "T",
    "AVG_Speed (M/min)", "Group ขาดจำนวน",
    "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "สถานะส่งงาน",
    "Detail", "สถานะซ่อมสรุป"
]

display_columns = [c for c in display_columns if c in fdf_display.columns]

st.dataframe(
    fdf_display[display_columns].sort_values("วันที่", ascending=False),
    use_container_width=True,
    height=520
)

st.caption("Shortage Dashboard | FINAL PROD VERSION")
