# =====================================
# Shortage Dashboard : DATA CHECK
# FINAL PROD VERSION
# =====================================

import streamlit as st
import pandas as pd
import plotly.express as px
st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.25);
    color: white;
    height: 140px;
}

.kpi-title {
    font-size: 14px;
    opacity: 0.85;
}

.kpi-value {
    font-size: 34px;
    font-weight: 700;
    margin-top: 10px;
}

.kpi-sub {
    font-size: 12px;
    opacity: 0.7;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

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

# ---------------- Sidebar ----------------
st.sidebar.header("🔎 ตัวกรองข้อมูล")

# ===== Manual Refresh =====
if st.sidebar.button("🔄 โหลดข้อมูลล่าสุดจาก Google Sheet"):
    st.cache_data.clear()
    st.rerun()

# ===== Default Date = Last 7 Days =====
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

# ---------------- Apply Filters ----------------
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
# SHORTAGE PERFORMANCE
# =========================
st.markdown(
    """
    <div style="
        padding: 14px 18px;
        border-radius: 14px;
        background: linear-gradient(90deg, #0f172a, #020617);
        margin: 12px 0 20px 0;
        border-left: 6px solid #ef4444;
    ">
        <h2 style="
            color: #f8fafc;
            margin: 0;
            font-weight: 700;
            letter-spacing: 1px;
        ">
            📊 SHORTAGE PERFORMANCE
        </h2>
        <p style="
            margin: 6px 0 0 0;
            color: #cbd5f5;
            font-size: 14px;
        ">
            ภาพรวมผลการผลิต (Order / ครบจำนวน / ขาดจำนวน / % ขาดจำนวน)
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# KPI : SHORTAGE PERFORMANCE (Power BI Style)
# =========================

order_total = len(fdf)
complete_qty = (fdf["สถานะผลิต"] == "ครบจำนวน").sum()
short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
short_pct = (short_qty / order_total * 100) if order_total > 0 else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ORDER TOTAL</div>
        <div class="kpi-value">{order_total:,}</div>
        <div class="kpi-sub">จำนวน Order ทั้งหมด</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ครบจำนวน</div>
        <div class="kpi-value">{complete_qty:,}</div>
        <div class="kpi-sub">ผลิตครบตามแผน</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ขาดจำนวน</div>
        <div class="kpi-value">{short_qty:,}</div>
        <div class="kpi-sub">Order ที่ผลิตไม่ครบ</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">% ขาดจำนวน</div>
        <div class="kpi-value">{short_pct:.1f}%</div>
        <div class="kpi-sub">เทียบ ORDER TOTAL</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =========================
# ⏰ AUTO INSIGHT (Executive Summary)
# =========================

st.markdown("### 🧠 Executive Insight")

# ป้องกันข้อมูลว่าง
if not fdf.empty and order_total > 0:

    shortage_pct = (short_qty / order_total) * 100

    # --- Insight ระดับความรุนแรง ---
    if shortage_pct >= 20:
        status_msg = "🔴 อยู่ในระดับวิกฤต"
    elif shortage_pct >= 15:
        status_msg = "🟡 ต้องเฝ้าระวัง"
    else:
        status_msg = "🟢 อยู่ในเกณฑ์ควบคุมได้"

    # --- สาเหตุหลัก ---
    top_cause = (
        fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]["Detail"]
        .value_counts()
        .head(1)
    )

    main_cause_text = (
        f"สาเหตุหลักคือ **{top_cause.index[0]}** ({top_cause.iloc[0]} Order)"
        if not top_cause.empty
        else "ยังไม่พบสาเหตุหลักชัดเจน"
    )

    # --- PDW ---
    pdw_col = "น้ำหนักของเหลือ PDW"
    pdw_text = ""

    if pdw_col in fdf.columns:
        pdw_sum = pd.to_numeric(
            fdf.loc[fdf["สถานะผลิต"] == "ขาดจำนวน", pdw_col],
            errors="coerce"
        ).fillna(0).sum()

        if pdw_sum > 0:
            pdw_text = f"น้ำหนักของเหลือรวม **{pdw_sum:,.2f} KG**"

    # --- แสดง Insight ---
    st.info(
        f"""
📊 **ภาพรวมช่วงเวลาที่เลือก**

- ORDER TOTAL : **{order_total:,}**
- ขาดจำนวน : **{short_qty:,} Order** (**{shortage_pct:.1f}%**) → {status_msg}  
- {main_cause_text}  
- {pdw_text}
        """
    )

else:
    st.info("ไม่มีข้อมูลเพียงพอสำหรับสรุปผลอัตโนมัติ")


# ---------------- TOP 10 + Donut ----------------
left, right = st.columns([2, 1])

# ===== TOP 10 Shortage (ALL INSIDE / ALWAYS VISIBLE) =====
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
        top10["label"] = (
            top10["จำนวน"].astype(str)
            + " ("
            + top10["เปอร์เซ็นต์"].astype(str)
            + "%)"
        )

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
            textposition="inside",          # 👉 อยู่ในแท่ง
            insidetextanchor="end",         # 👉 ชิดปลายแท่ง
            textfont=dict(
                color="blue",               # 👉 สีน้ำเงิน
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

# ---------------- STACKED BAR ----------------
st.divider()
st.subheader("📊 เปอร์เซ็นต์ ครบจำนวน / ขาดจำนวน")

trend = fdf.copy()

if not trend.empty:

    # ===== สร้างช่วงเวลา + key สำหรับเรียง =====
    if period == "รายวัน":
        trend["ช่วง_dt"] = trend["วันที่"].dt.normalize()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%d/%m/%Y")

    elif period == "รายสัปดาห์":
        trend["ช่วง_dt"] = trend["วันที่"] - pd.to_timedelta(
            trend["วันที่"].dt.weekday, unit="D"
        )
        trend["ช่วง"] = (
            "Week "
            + trend["ช่วง_dt"].dt.isocalendar().week.astype(str)
            + " / "
            + trend["ช่วง_dt"].dt.year.astype(str)
        )

    elif period == "รายเดือน":
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("M").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.strftime("%b %Y")

    elif period == "รายปี":
        trend["ช่วง_dt"] = trend["วันที่"].dt.to_period("Y").dt.to_timestamp()
        trend["ช่วง"] = trend["ช่วง_dt"].dt.year.astype(str)

    # ===== สรุปข้อมูล =====
    summary = (
        trend
        .groupby(["ช่วง_dt", "ช่วง", "สถานะผลิต"])
        .size()
        .reset_index(name="จำนวน")
    )

    # ===== รวมยอดต่อช่วง =====
    total = (
        summary
        .groupby(["ช่วง_dt", "ช่วง"])["จำนวน"]
        .sum()
        .reset_index(name="รวม")
    )

    summary = summary.merge(total, on=["ช่วง_dt", "ช่วง"])

    summary["เปอร์เซ็นต์"] = (summary["จำนวน"] / summary["รวม"] * 100).round(1)
    summary["label"] = (
        summary["จำนวน"].astype(str)
        + " ("
        + summary["เปอร์เซ็นต์"].astype(str)
        + "%)"
    )

    # ===== ล็อกลำดับสี =====
    summary["สถานะผลิต"] = pd.Categorical(
        summary["สถานะผลิต"],
        categories=["ครบจำนวน", "ขาดจำนวน"],
        ordered=True
    )

    # ===== เรียงตามเวลา =====
    summary = summary.sort_values("ช่วง_dt")

    # ===== Plot =====
    fig_stack = px.bar(
        summary,
        x="ช่วง",
        y="เปอร์เซ็นต์",
        color="สถานะผลิต",
        text="label",
        barmode="stack",
        category_orders={
            "สถานะผลิต": ["ครบจำนวน", "ขาดจำนวน"]
        },
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

    fig_stack.update_traces(
        textposition="inside",
        textfont_size=13
    )

    st.plotly_chart(fig_stack, use_container_width=True)
    
    # ---------------- SHORTAGE ISSUE SUMMARY ----------------
st.divider()
st.subheader("🛠️ สรุปปัญหาสถานะซ่อม (เฉพาะงานขาดจำนวน)")

# =========================
# SUMMARY : ขาดจำนวน + PDW (ROW)
# =========================
c1, c2 = st.columns(2)

# ---- ขาดจำนวน ----
with c1:
    short_qty = (fdf["สถานะผลิต"] == "ขาดจำนวน").sum()
    st.markdown("### ❌ ขาดจำนวน")
    st.metric(label="", value=f"{short_qty:,} ORDER")

# ---- น้ำหนักของเหลือ PDW ----
with c2:
    pdw_col = "น้ำหนักของเหลือ PDW"
    pdw_total = 0.0

    if pdw_col in fdf.columns:
        pdw_df = fdf[
            (fdf["สถานะผลิต"] == "ขาดจำนวน") &
            (fdf[pdw_col].notna())
        ].copy()

        pdw_df[pdw_col] = pd.to_numeric(
            pdw_df[pdw_col],
            errors="coerce"
        ).fillna(0)

        pdw_total = pdw_df[pdw_col].sum()

    st.markdown("### ⚖️ น้ำหนักของเหลือ PDW (รวม)")
    st.metric(label="", value=f"{pdw_total:,.2f} KG")

# =========================
# ISSUE SUMMARY TABLE + PIE
# =========================
if "สถานะซ่อมสรุป" in fdf.columns:

    issue_df = (
        fdf[fdf["สถานะผลิต"] == "ขาดจำนวน"]
        .dropna(subset=["สถานะซ่อมสรุป"])
        .groupby("สถานะซ่อมสรุป")
        .size()
        .reset_index(name="จำนวน")
        .sort_values("จำนวน", ascending=False)
        .reset_index(drop=True)
    )

    if not issue_df.empty:
        c1, c2 = st.columns([1, 1])

        with c1:
            st.markdown("### 📋 ตารางสรุปปัญหา")
            st.dataframe(issue_df, use_container_width=True, height=350)

        with c2:
            fig_issue = px.pie(
                issue_df,
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
        st.info("ไม่มีข้อมูลสถานะซ่อมสำหรับงานขาดจำนวนในช่วงที่เลือก")
else:
    st.warning("ไม่พบคอลัมน์ 'สถานะซ่อมสรุป'")

# ---------------- Table ----------------
st.divider()
st.subheader("📋 รายละเอียด Order")

fdf_display = fdf.copy()
fdf_display["วันที่"] = fdf_display["วันที่"].dt.strftime("%d/%m/%Y")

display_columns = [
    "วันที่", "ลำดับที่", "MC", "กะ", "PDR No.", "ชื่อลูกค้า",
    "M1", "M3", "M5", "ลอน",
    "ความยาวทั้งหมด(เมตร)", "ความยาว/แผ่น(มม)", "T",
    "AVG_Speed (M/min)", "Group ขาดจำนวน",
    "จำนวนที่ลูกค้าต้องการ", "ขาดจำนวน", "สถานะส่งงาน", "Detail", "สถานะซ่อมสรุป"
]

display_columns = [c for c in display_columns if c in fdf_display.columns]

st.dataframe(
    fdf_display[display_columns].sort_values("วันที่", ascending=False),
    use_container_width=True,
    height=520
)

st.caption("Shortage Dashboard | FINAL PROD VERSION")
