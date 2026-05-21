import streamlit as st
import pandas as pd
from utils.api import get_all_applications, update_application_status

st.set_page_config(layout="wide", page_title="Loan Officer", page_icon="👨‍💼")
st.title("👨‍💼 Loan Officer Dashboard")

response = get_all_applications()

if response.status_code != 200:
    st.error("Failed to fetch applications")
    st.stop()

applications = response.json()["applications"]

if not applications:
    st.warning("No applications found")
    st.stop()

df = pd.DataFrame(applications)

# --- Filters ---
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.multiselect("Filter by Status", df["status"].unique(), default=list(df["status"].unique()))
with col2:
    risk_filter = st.multiselect("Filter by Risk Band", df["risk_band"].unique(), default=list(df["risk_band"].unique()))
with col3:
    loan_filter = st.multiselect("Filter by Loan Type", df["loan_type"].unique(), default=list(df["loan_type"].unique()))

filtered = df[
    df["status"].isin(status_filter) &
    df["risk_band"].isin(risk_filter) &
    df["loan_type"].isin(loan_filter)
]

st.markdown(f"Showing **{len(filtered)}** of **{len(df)}** applications")
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.divider()

# --- Update Status ---
st.subheader("✏️ Update Application Status")

col1, col2 = st.columns(2)
with col1:
    app_id = st.number_input("Application ID", min_value=1)
    status = st.selectbox("New Status", ["approved", "rejected", "under_review"],
                           format_func=lambda x: x.replace("_", " ").title())
with col2:
    notes = st.text_area("Notes", height=120, placeholder="Add decision notes here...")

if st.button("Update Status", type="primary"):
    with st.spinner("Updating..."):
        resp = update_application_status(app_id, status, notes)
    if resp.status_code == 200:
        st.success(f"✅ Application {app_id} updated to **{status}**")
    else:
        st.error("Update failed")
        st.json(resp.json())