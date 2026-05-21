import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api import get_all_applications

st.set_page_config(layout="wide", page_title="Admin Dashboard", page_icon="📊")

st.markdown("""
<style>
    .section-title {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 Admin Dashboard")
st.divider()

response = get_all_applications()

if response.status_code != 200:
    st.error("Failed to fetch applications")
    st.stop()

applications = response.json()["applications"]

if not applications:
    st.warning("No applications yet.")
    st.stop()

df = pd.DataFrame(applications)
df["created_at"] = pd.to_datetime(df["created_at"])

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

st.markdown('<div class="section-title">📈 Overview</div>', unsafe_allow_html=True)

total        = len(df)
approved     = len(df[df["status"] == "approved"])
rejected     = len(df[df["status"] == "rejected"])
under_review = len(df[df["status"] == "under_review"])
approval_rate = round((approved / total) * 100, 1) if total else 0
avg_cibil    = round(df["cibil_score"].mean())
total_disbursed = int(df["approved_amount"].sum())
high_fraud   = len(df[df["fraud_probability"] > 0.7])

c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
c1.metric("Total",         total)
c2.metric("Approved",      approved, delta=f"{approval_rate}%")
c3.metric("Rejected",      rejected)
c4.metric("Under Review",  under_review)
c5.metric("Avg CIBIL",     avg_cibil)
c6.metric("Disbursed",     f"₹{total_disbursed:,}")
c7.metric("High Fraud",    high_fraud, delta="flagged", delta_color="inverse")
c8.metric("Approval Rate", f"{approval_rate}%")

st.divider()

# ---------------------------------------------------------------------------
# Row 1 — Status donut + Risk band bar
# ---------------------------------------------------------------------------

st.markdown('<div class="section-title">🔍 Portfolio Breakdown</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

STATUS_COLORS = {
    "approved":     "#22c55e",
    "rejected":     "#ef4444",
    "under_review": "#f59e0b",
    "pending":      "#94a3b8",
    "disbursed":    "#2563eb",
}

RISK_COLORS = {
    "LOW":       "#22c55e",
    "MEDIUM":    "#f59e0b",
    "HIGH":      "#f97316",
    "VERY_HIGH": "#ef4444",
}

with col1:
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    fig1 = px.pie(
        status_counts,
        names="status",
        values="count",
        color="status",
        color_discrete_map=STATUS_COLORS,
        hole=0.55,
        title="Application Status"
    )
    fig1.update_traces(textposition="outside", textinfo="percent+label")
    fig1.update_layout(
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
        title_font_color="#e2e8f0",
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    risk_counts = df["risk_band"].value_counts().reset_index()
    risk_counts.columns = ["risk_band", "count"]

    fig2 = px.bar(
        risk_counts,
        x="risk_band",
        y="count",
        color="risk_band",
        color_discrete_map=RISK_COLORS,
        text="count",
        title="Risk Band Distribution"
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Applications",
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
        title_font_color="#e2e8f0",
        xaxis=dict(gridcolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b"),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Row 2 — Fraud scatter + Applications over time
# ---------------------------------------------------------------------------

st.markdown('<div class="section-title">🕵️ Fraud & Trends</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig3 = px.scatter(
        df,
        x="fraud_probability",
        y="ml_credit_score",
        color="risk_band",
        color_discrete_map=RISK_COLORS,
        size="requested_amount",
        hover_data=["applicant_name", "status", "loan_type"],
        opacity=0.8,
        title="Fraud Probability vs ML Credit Score"
    )
    fig3.add_vline(
        x=0.7,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text="Fraud threshold",
        annotation_font_color="#ef4444"
    )
    fig3.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
        title_font_color="#e2e8f0",
        xaxis=dict(gridcolor="#1e293b", title="Fraud Probability"),
        yaxis=dict(gridcolor="#1e293b", title="ML Credit Score"),
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").size().reset_index(name="count")

    fig4 = px.line(
        monthly,
        x="month",
        y="count",
        markers=True,
        line_shape="spline",
        title="Applications Over Time"
    )
    fig4.update_traces(
        line_color="#2563eb",
        marker_color="#2563eb",
        marker_size=8,
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.1)"
    )
    fig4.update_layout(
        margin=dict(t=40, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#94a3b8",
        title_font_color="#e2e8f0",
        xaxis=dict(gridcolor="#1e293b", title=""),
        yaxis=dict(gridcolor="#1e293b", title="Applications"),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Searchable table
# ---------------------------------------------------------------------------

st.markdown('<div class="section-title">📋 All Applications</div>', unsafe_allow_html=True)

search = st.text_input("Search by name or email", placeholder="Type to filter...")

display_df = df.copy()
if search:
    mask = (
        display_df["applicant_name"].str.contains(search, case=False, na=False) |
        display_df["applicant_email"].str.contains(search, case=False, na=False)
    )
    display_df = display_df[mask]

st.caption(f"Showing {len(display_df)} of {total} applications")

st.dataframe(
    display_df[[
        "id", "applicant_name", "loan_type",
        "requested_amount", "cibil_score",
        "risk_band", "ml_credit_score",
        "fraud_probability", "status", "created_at"
    ]].sort_values("created_at", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id":                "ID",
        "applicant_name":    "Name",
        "loan_type":         "Type",
        "requested_amount":  st.column_config.NumberColumn("Amount (₹)", format="₹%d"),
        "cibil_score":       "CIBIL",
        "risk_band":         "Risk",
        "ml_credit_score":   st.column_config.NumberColumn("ML Score", format="%.2f"),
        "fraud_probability": st.column_config.NumberColumn("Fraud %", format="%.2f"),
        "status":            "Status",
        "created_at":        st.column_config.DatetimeColumn("Applied At", format="DD MMM YYYY"),
    }
)