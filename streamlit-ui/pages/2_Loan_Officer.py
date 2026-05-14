
import streamlit as st
import pandas as pd
from utils.api import get_all_applications, update_application_status

st.title("👨‍💼 Loan Officer Dashboard")

response = get_all_applications()

if response.status_code == 200:

    data = response.json()

    applications = data["applications"]

    if applications:

        df = pd.DataFrame(applications)

        st.dataframe(df, use_container_width=True)

        st.subheader("Update Application Status")

        app_id = st.number_input("Application ID", min_value=1)

        status = st.selectbox(
            "New Status",
            ["approved", "rejected", "under_review"]
        )

        notes = st.text_area("Notes")

        if st.button("Update Status"):

            resp = update_application_status(
                app_id,
                status,
                notes
            )

            if resp.status_code == 200:
                st.success("Status Updated")
                st.json(resp.json())
            else:
                st.error("Update Failed")
                st.json(resp.json())

    else:
        st.warning("No applications found")

else:
    st.error("Failed to fetch applications")