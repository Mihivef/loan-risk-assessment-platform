


import os
import requests

BASE_URL = os.getenv(
    "GO_BACKEND_URL",
    "http://go-gateway:8080"
)
TOKENS = {
    "customer": "token-customer",
    "loan_officer": "token-loan-officer",
    "admin": "token-admin"
}


def get_headers(role="customer"):
    return {
        "Authorization": TOKENS[role],
        "Content-Type": "application/json"
    }


def submit_application(payload):
    return requests.post(
        f"{BASE_URL}/api/applications",
        json=payload,
        headers=get_headers("customer")
    )


def get_all_applications():
    return requests.get(
        f"{BASE_URL}/api/applications",
        headers=get_headers("loan_officer")
    )


def update_application_status(app_id, status, notes=""):
    payload = {
        "status": status,
        "notes": notes
    }

    return requests.put(
        f"{BASE_URL}/api/applications/{app_id}/status",
        json=payload,
        headers=get_headers("loan_officer")
    )


def get_dashboard_stats():
    return requests.get(
        f"{BASE_URL}/api/dashboard/stats",
        headers=get_headers("admin")
    )


def calculate_emi(principal, rate, tenure):
    return requests.get(
        f"{BASE_URL}/api/emi",
        params={
            "principal": principal,
            "rate": rate,
            "tenure_months": tenure
        },
        headers=get_headers("customer")
    )