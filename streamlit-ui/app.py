import streamlit as st

st.set_page_config(
    page_title="Loan Risk Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main {
    background-color: #0E1117;
}

.metric-card {
    background-color: #1E1E1E;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #333;
}

.big-font {
    font-size:22px !important;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

st.title("Loan Risk Assessment Platform")

st.markdown("""
### Enterprise Banking Platform

This platform demonstrates:

- Go Gin API Gateway
- Python ML Credit Scoring
- Fraud Detection Engine
- Java Policy Engine
- Real-time Loan Decisions
- Admin Analytics Dashboard
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("👤 Customer Portal\n\nSubmit loan applications")

with col2:
    st.warning("👨‍💼 Loan Officer\n\nReview and approve applications")

with col3:
    st.success("📊 Admin Dashboard\n\nView analytics and insights")

st.divider()

st.markdown("### Use the sidebar to navigate between modules.")