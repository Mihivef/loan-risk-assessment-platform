

import streamlit as st
from utils.api import submit_application

st.set_page_config(layout="wide")

st.title("Customer Loan Application")

st.markdown("Fill in your details to receive an instant loan decision.")

with st.container(border=True):

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Personal Information")

        applicant_name = st.text_input("Full Name")
        applicant_email = st.text_input("Email Address")
        applicant_phone = st.text_input("Phone Number")

        loan_type = st.selectbox(
            "Loan Type",
            ["personal", "home", "vehicle", "business", "education"]
        )

        purpose = st.text_area("Purpose of Loan")

    with col2:
        st.subheader("Financial Information")

        requested_amount = st.number_input(
            "Requested Amount",
            min_value=10000,
            step=10000
        )

        tenure_months = st.slider(
            "Loan Tenure (Months)",
            6,
            360,
            36
        )

        annual_income = st.number_input(
            "Annual Income",
            min_value=100000,
            step=50000
        )

        existing_monthly_emis = st.number_input(
            "Existing Monthly EMIs",
            min_value=0,
            step=1000
        )

        employment_type = st.selectbox(
            "Employment Type",
            ["salaried", "self_employed", "business_owner"]
        )

        employer_name = st.text_input("Employer Name")

        years_employed = st.slider(
            "Years Employed",
            0,
            40,
            5
        )

        cibil_score = st.slider(
            "CIBIL Score",
            300,
            900,
            750
        )

    submit = st.button("Submit Application")

if submit:

    payload = {
        "applicant_name": applicant_name,
        "applicant_email": applicant_email,
        "applicant_phone": applicant_phone,
        "loan_type": loan_type,
        "requested_amount": requested_amount,
        "tenure_months": tenure_months,
        "purpose": purpose,
        "annual_income": annual_income,
        "existing_monthly_emis": existing_monthly_emis,
        "employment_type": employment_type,
        "employer_name": employer_name,
        "years_employed": years_employed,
        "cibil_score": cibil_score
    }

    response = submit_application(payload)

    if response.status_code == 201:

        data = response.json()

        st.success("Application Processed Successfully")

        app = data["application"]
        pipeline = data["pipeline"]

        st.subheader("Decision")

        c1, c2, c3 = st.columns(3)

        c1.metric("Status", app["status"])
        c2.metric("Risk Band", app["risk_band"])
        c3.metric("ML Score", round(app["ml_credit_score"], 2))

        st.subheader("Pipeline Analysis")

        st.json(pipeline)

        st.subheader("Loan Details")

        st.json(app)

    else:
        st.error("Failed to submit application")
        st.json(response.json())
