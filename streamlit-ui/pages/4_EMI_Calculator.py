import streamlit as st
import pandas as pd
import plotly.express as px
from utils.api import calculate_emi

st.set_page_config(layout="wide", page_title="EMI Calculator", page_icon="💰")
st.title("💰 EMI Calculator")

col1, col2, col3 = st.columns(3)
with col1:
    principal = st.number_input("Principal Amount (₹)", min_value=10000.0, step=10000.0, value=500000.0)
with col2:
    rate = st.number_input("Annual Interest Rate (%)", min_value=1.0, value=10.5)
with col3:
    tenure = st.number_input("Tenure (Months)", min_value=1, value=24)

if st.button("Calculate EMI", type="primary"):
    response = calculate_emi(principal, rate, tenure)

    if response.status_code == 200:
        data = response.json()

        c1, c2, c3 = st.columns(3)
        c1.metric("Monthly EMI", f"₹{data['monthly_emi']:,.2f}")
        c2.metric("Total Payable", f"₹{data['total_payable']:,.2f}")
        c3.metric("Total Interest", f"₹{data['total_interest']:,.2f}",
                   delta=f"{round(data['total_interest']/principal*100, 1)}% of principal",
                   delta_color="inverse")

        # Pie chart — principal vs interest
        fig = px.pie(
            values=[principal, data["total_interest"]],
            names=["Principal", "Interest"],
            title="Principal vs Interest Breakdown",
            color_discrete_sequence=["#2563eb", "#f59e0b"]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Failed to calculate EMI")