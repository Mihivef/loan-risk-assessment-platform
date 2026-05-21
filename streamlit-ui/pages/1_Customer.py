import streamlit as st
from utils.api import submit_application

st.set_page_config(layout="wide", page_title="Loan Application", page_icon="🏦")

st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        height: 3em !important;
        width: 100% !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
    }
    .stButton > button:hover { opacity: 0.88 !important; }

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

    .cibil-bar-wrap {
        background: #0f172a;
        border-radius: 999px;
        height: 8px;
        width: 100%;
        margin-top: 6px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)



st.markdown("# 🏦 Loan Application")
st.markdown("Complete the form below to receive an instant decision.")
st.divider()



st.markdown('<div class="section-title">👤 Personal Information</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    applicant_name = st.text_input("Full Name", value="")
with col2:
    applicant_email = st.text_input("Email Address", value="")
with col3:
    applicant_phone = st.text_input("Phone Number", value="")

st.divider()



st.markdown('<div class="section-title">💰 Loan Details</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    loan_type = st.selectbox(
        "Loan Type",
        ["", "personal", "home", "vehicle", "business", "education"],
        format_func=lambda x: "Select loan type" if x == "" else x.title()
    )
with col2:
    requested_amount = st.number_input(
        "Requested Amount (₹)",
        min_value=0,
        step=10000,
        value=0,
        format="%d"
    )
with col3:
    tenure_months = st.number_input(
        "Tenure (Months)",
        min_value=6,
        max_value=360,
        value=None,
        placeholder="e.g. 36",
        step=6
    )

purpose = st.text_area(
    "Purpose of Loan",
    value="",
    placeholder="Briefly describe why you need this loan",
    height=80
)

st.divider()



st.markdown('<div class="section-title">📊 Financial Information</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    annual_income = st.number_input(
        "Annual Income (₹)",
        min_value=0,
        step=50000,
        value=0,
        format="%d"
    )
with col2:
    existing_monthly_emis = st.number_input(
        "Existing Monthly EMIs (₹)",
        min_value=0,
        step=1000,
        value=0,
        format="%d"
    )
with col3:
    cibil_score = st.number_input(
        "CIBIL Score",
        min_value=300,
        max_value=900,
        value=None,
        placeholder="300 – 900",
        step=1
    )

if cibil_score:
    pct = int(((cibil_score - 300) / 600) * 100)
    if cibil_score >= 750:
        bar_color, label = "#22c55e", f"✅ Excellent ({cibil_score}) — strong approval chances"
    elif cibil_score >= 650:
        bar_color, label = "#f59e0b", f"⚠️ Fair ({cibil_score}) — moderate approval chances"
    else:
        bar_color, label = "#ef4444", f"❌ Poor ({cibil_score}) — low approval chances"

    st.markdown(f"""
    <div style="margin-top:-8px; margin-bottom:8px;">
        <div style="color:#64748b; font-size:12px; margin-bottom:5px;">{label}</div>
        <div class="cibil-bar-wrap">
            <div style="height:100%; width:{pct}%; background:{bar_color};
                        border-radius:999px; transition:width 0.4s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()



st.markdown('<div class="section-title">💼 Employment Details</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    employment_type = st.selectbox(
        "Employment Type",
        ["", "salaried", "self_employed", "business_owner"],
        format_func=lambda x: "Select type" if x == "" else x.replace("_", " ").title()
    )
with col2:
    employer_name = st.text_input("Employer / Company Name", value="")
with col3:
    years_employed = st.number_input(
        "Years Employed",
        min_value=0,
        max_value=40,
        value=None,
        placeholder="e.g. 3",
        step=1
    )

st.divider()



_, btn_col, _ = st.columns([3, 2, 3])
with btn_col:
    submit = st.button("Submit Application")



if submit:
    errors = []
    if not applicant_name:            errors.append("Full Name is required")
    if not applicant_email:           errors.append("Email Address is required")
    if not applicant_phone:           errors.append("Phone Number is required")
    if not loan_type:                 errors.append("Loan Type is required")
    if not purpose or len(purpose) < 10: errors.append("Purpose must be at least 10 characters")
    if not requested_amount:          errors.append("Requested Amount is required")
    if not tenure_months:             errors.append("Tenure is required")
    if not annual_income:             errors.append("Annual Income is required")
    if not cibil_score:               errors.append("CIBIL Score is required")
    if not employment_type:           errors.append("Employment Type is required")
    if not employer_name:             errors.append("Employer Name is required")
    if years_employed is None:        errors.append("Years Employed is required")

    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Analysing your application..."):
            payload = {
                "applicant_name":        applicant_name,
                "applicant_email":       applicant_email,
                "applicant_phone":       applicant_phone,
                "loan_type":             loan_type,
                "requested_amount":      requested_amount,
                "tenure_months":         int(tenure_months),
                "purpose":               purpose,
                "annual_income":         annual_income,
                "existing_monthly_emis": existing_monthly_emis,
                "employment_type":       employment_type,
                "employer_name":         employer_name,
                "years_employed":        int(years_employed),
                "cibil_score":           int(cibil_score),
            }
            response = submit_application(payload)

        if response.status_code == 201:
            data     = response.json()
            app      = data["application"]
            pipeline = data["pipeline"]
            status   = app["status"]

            st.divider()

            if status == "approved":
                st.balloons()
                st.success("✅ Your loan has been approved!")
            elif status == "rejected":
                st.error("❌ Your application was not approved.")
            else:
                st.warning("⏳ Your application is under review.")

            st.divider()

            st.markdown('<div class="section-title">📋 Decision Summary</div>', unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Decision",          status.replace("_", " ").title())
            c2.metric("Risk Band",         app["risk_band"])
            c3.metric("ML Credit Score",   round(app["ml_credit_score"], 2))
            c4.metric("Fraud Probability", round(app["fraud_probability"], 3))

            if status == "approved":
                st.divider()
                st.markdown('<div class="section-title">💳 Loan Offer</div>', unsafe_allow_html=True)

                l1, l2, l3 = st.columns(3)
                l1.metric("Approved Amount", f"₹{int(app['approved_amount']):,}")
                l2.metric("Interest Rate",   f"{app['interest_rate_percent']}%")
                l3.metric("Monthly EMI",     f"₹{app['monthly_emi']:,.2f}")

        else:
            st.error("Submission failed — please try again.")
            st.json(response.json())