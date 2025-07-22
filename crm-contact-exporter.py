import streamlit as st
import requests
import base64

# ======= CONFIGURATION =======
API_KEY = "your_fub_api_key_here"  # Replace with your actual API key
API_URL = "https://api.followupboss.com/v1"

# ======= AUTH HEADER =======
token = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {token}",
    "Accept": "application/json"
}

# ======= UTILITY FUNCTIONS =======

def fetch_agents():
    try:
        response = requests.get(f"{API_URL}/users", headers=HEADERS)
        response.raise_for_status()
        agents = response.json().get("users", [])
        return agents
    except Exception as e:
        st.error(f"Failed to fetch agents: {e}")
        return []

def fetch_ponds():
    try:
        response = requests.get(f"{API_URL}/ponds", headers=HEADERS)
        response.raise_for_status()
        ponds = response.json().get("ponds", [])
        return ponds
    except Exception as e:
        st.error(f"Failed to fetch ponds: {e}")
        return []

def fetch_contacts_by_pond(pond_id):
    try:
        params = {"pondId": pond_id}
        response = requests.get(f"{API_URL}/people", headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get("people", [])
    except Exception as e:
        st.error(f"Error fetching contacts by pond: {e}")
        return []

# ======= STREAMLIT APP =======
st.title("Follow Up Boss: Contacts by Pond or Agent")

agents = fetch_agents()
ponds = fetch_ponds()

# Dropdown filters
option = st.radio("Filter contacts by agent or pond:", ["Agent", "Pond"])

selected_agent_id = None
selected_pond_id = None

if option == "Agent":
    agent_options = {f"{a['firstName']} {a['lastName']}": a["id"] for a in agents}
    selected_agent = st.selectbox("Select an agent", list(agent_options.keys()))
    selected_agent_id = agent_options.get(selected_agent)

elif option == "Pond":
    pond_options = {p["name"]: p["id"] for p in ponds}
    selected_pond = st.selectbox("Select a pond", list(pond_options.keys()))
    selected_pond_id = pond_options.get(selected_pond)

if st.button("Fetch Contacts"):
    if selected_pond_id:
        contacts = fetch_contacts_by_pond(selected_pond_id)
        st.success(f"Fetched {len(contacts)} contacts from pond.")
        for contact in contacts:
            st.write(contact.get("name", "Unnamed"), "-", contact.get("email", "No email"))
    elif selected_agent_id:
        st.warning("Agent filter not implemented yet.")
    else:
        st.warning("Please select a filter option.")
