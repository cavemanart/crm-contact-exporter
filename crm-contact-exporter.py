import streamlit as st
import requests
import base64
import json

# ===== CONFIG =====
API_KEY = "your_api_key_here"  # Replace with your real Follow Up Boss API key
API_URL = "https://api.followupboss.com/v1"

# ===== Basic Auth Header =====
def get_auth_header():
    token = base64.b64encode(f"{API_KEY}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json"
    }

# ===== API Fetchers with Logging =====
def fetch_agents():
    try:
        response = requests.get(f"{API_URL}/users", headers=get_auth_header())
        response.raise_for_status()
        return response.json().get("users", [])
    except Exception as e:
        st.exception(e)
        return []

def fetch_ponds():
    try:
        response = requests.get(f"{API_URL}/ponds", headers=get_auth_header())
        response.raise_for_status()
        return response.json().get("ponds", [])
    except Exception as e:
        st.exception(e)
        return []

def fetch_contacts_by_pond(pond_id):
    try:
        params = {"pondId": pond_id}
        response = requests.get(f"{API_URL}/people", headers=get_auth_header(), params=params)
        response.raise_for_status()
        return response.json().get("people", [])
    except Exception as e:
        st.exception(e)
        return []

# ===== Streamlit App UI =====
st.title("📇 FUB Contacts by Pond")

# Fetch agents and ponds once
agents = fetch_agents()
ponds = fetch_ponds()

# Choose filter type
filter_type = st.radio("Filter contacts by:", ["Pond", "Agent (Coming Soon)"])

if filter_type == "Pond":
    pond_dict = {pond["name"]: pond["id"] for pond in ponds}
    pond_name = st.selectbox("Choose a pond:", list(pond_dict.keys()))
    selected_pond_id = pond_dict[pond_name]

    if st.button("Fetch Contacts"):
        contacts = fetch_contacts_by_pond(selected_pond_id)
        if contacts:
            st.success(f"Found {len(contacts)} contacts in {pond_name}")
            for c in contacts:
                st.write(f"**{c.get('name')}** — {c.get('email', 'No email')} — {c.get('stage', '')}")
        else:
            st.warning("No contacts found or request failed.")
