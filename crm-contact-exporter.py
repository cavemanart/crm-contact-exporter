import streamlit as st
import requests
import pandas as pd

# Replace with your Follow Up Boss API key
FUB_API_KEY = st.secrets.get("FUB_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.followupboss.com/v1"

headers = {
    "Authorization": f"Basic {FUB_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def fetch_agents():
    try:
        res = requests.get(f"{BASE_URL}/users", headers=headers)
        res.raise_for_status()
        agents = res.json()
        return [
            {"id": a["id"], "name": a["name"]}
            for a in agents if a.get("isAgent")
        ]
    except Exception as e:
        st.error(f"Failed to fetch agents: {e}")
        return []


def fetch_ponds():
    try:
        res = requests.get(f"{BASE_URL}/ponds", headers=headers)
        res.raise_for_status()
        ponds = res.json().get("ponds", [])
        return [{"id": p["id"], "name": p["name"]} for p in ponds]
    except Exception as e:
        st.error(f"Failed to fetch ponds: {e}")
        return []


def fetch_contacts_by_agent(agent_id):
    url = f"{BASE_URL}/people?assignedTo={agent_id}&limit=100"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Error fetching contacts by agent: {res.text}")
        return []

    return res.json().get("people", [])


def fetch_contacts_by_pond(pond_id):
    url = f"{BASE_URL}/ponds/{pond_id}/people?limit=100"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Error fetching contacts by pond: {res.text}")
        return []

    return res.json().get("people", [])


# --- Streamlit UI ---

st.title("Follow Up Boss Contact Exporter")

# Load agents and ponds
agents = fetch_agents()
ponds = fetch_ponds()

agent_options = {a["name"]: a["id"] for a in agents}
pond_options = {p["name"]: p["id"] for p in ponds}

tab1, tab2 = st.tabs(["Agent", "Pond"])

contacts = []

with tab1:
    agent_name = st.selectbox("Select an agent", list(agent_options.keys()))
    if st.button("Fetch Contacts for Agent"):
        agent_id = agent_options[agent_name]
        contacts = fetch_contacts_by_agent(agent_id)

with tab2:
    pond_name = st.selectbox("Select a pond", list(pond_options.keys()))
    if st.button("Fetch Contacts for Pond"):
        pond_id = pond_options[pond_name]
        contacts = fetch_contacts_by_pond(pond_id)

# Show results
if contacts:
    st.success(f"Fetched {len(contacts)} contacts")
    df = pd.DataFrame([
        {
            "Name": c.get("name"),
            "Email": c.get("emails", [{}])[0].get("value", ""),
            "Phone": c.get("phones", [{}])[0].get("value", ""),
            "Created": c.get("created"),
            "Stage": c.get("stage"),
            "Assigned To": c.get("assignedTo", {}).get("name", "")
        }
        for c in contacts
    ])
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "contacts.csv", "text/csv")
else:
    st.warning("No contacts to display")
