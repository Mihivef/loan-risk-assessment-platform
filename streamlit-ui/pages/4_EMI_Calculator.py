
import streamlit as st
from utils.api import calculate_emi

st.title("💰 EMI Calculator")

principal = st.number_input(
    "Principal Amount",
    min_value=10000.0
)

rate = st.number_input(
    "Annual Interest Rate (%)",
    min_value=1.0
)

tenure = st.number_input(
    "Tenure (Months)",
    min_value=1
)

if st.button("Calculate EMI"):

    response = calculate_emi(
        principal,
        rate,
        tenure
    )

    if response.status_code == 200:

        data = response.json()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Monthly EMI",
            f"₹ {data['monthly_emi']:,.2f}"
        )

        c2.metric(
            "Total Payable",
            f"₹ {data['total_payable']:,.2f}"
        )

        c3.metric(
            "Total Interest",
            f"₹ {data['total_interest']:,.2f}"
        )

    else:
        st.error("Failed to calculate EMI")