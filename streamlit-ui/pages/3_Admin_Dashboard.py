

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api import get_all_applications

st.title("📊 Admin Analytics Dashboard")

response = get_all_applications()

if response.status_code == 200:

    applications = response.json()["applications"]

    if len(applications) == 0:
        st.warning("No applications yet")
        st.stop()

    df = pd.DataFrame(applications)

    total = len(df)
    approved = len(df[df["status"] == "approved"])
    rejected = len(df[df["status"] == "rejected"])
    pending = len(df[df["status"] == "pending"])

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Applications", total)
    c2.metric("Approved", approved)
    c3.metric("Rejected", rejected)
    c4.metric("Pending", pending)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Band Distribution")

        fig1 = px.pie(
            df,
            names="risk_band",
            title="Risk Categories"
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Loan Type Distribution")

        fig2 = px.histogram(
            df,
            x="loan_type"
        )

        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader("Fraud Probability Analysis")

    fig3 = px.scatter(
        df,
        x="fraud_probability",
        y="ml_credit_score",
        color="risk_band",
        title="Fraud Probability vs ML Credit Score"
    )

    st.plotly_chart(fig3, use_container_width=True)
