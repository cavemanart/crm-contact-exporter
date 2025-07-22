import streamlit as st
import requests
import time

# ------------------------
# Utility: Auth Header
# ------------------------
def get_auth_header(api_key):
    return {"Authorization": f"Bearer {api_key}"}

# ------------------------
# Get all agents
# ------------------------
def fetch_agents(api_key):
    url = "https://api.followupboss.com/v1/users"
    headers = get_auth_header(api_key)
    agents = []
    offset = 0
    limit = 100

    with st.spinner("Fetching agents..."):
        while True:
            params = {"offset": offset, "limit": limit}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error("Failed to fetch agents")
                return []
            data = response.json()
            agents.extend(data.get("users", []))
            if len(data.get("users", [])) < limit:
                break
            offset += limit
            time.sleep(0.2)
    st.success(f"Fetched {len(agents)} agents")
    return agents

# ------------------------
# Get all ponds
# ------------------------
def fetch_ponds(api_key):
    url = "https://api.followupboss.com/v1/ponds"
    headers = get_auth_header(api_key)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch ponds")
        return []
    data = response.json()
    st.success(f"Fetched {len(data.get('ponds', []))} ponds")
    return data.get("ponds", [])

# ------------------------
# Get contacts by agent
# ------------------------
def fetch_contacts_by_agent(api_key, agent_name):
    url = "https://api.followupboss.com/v1/people"
    headers = get_auth_header(api_key)
    contacts = []
    offset = 0
    limit = 100

    with st.spinner(f"Fetching contacts assigned to {agent_name}..."):
        while True:
            params = {"offset": offset, "limit": limit}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Failed to fetch contacts: {response.status_code}")
                return []
            data = response.json()
            people = data.get("people", [])
            for person in people:
                assigned = person.get("assignedTo", {})
                if assigned and assigned.get("name") == agent_name:
                    contacts.append(person)
            if len(people) < limit:
                break
            offset += limit
            time.sleep(0.2)
    st.success(f"Found {len(contacts)} contacts assigned to {agent_name}")
    return contacts

# ------------------------
# Get contacts by pond
# ------------------------
def fetch_contacts_by_pond(api_key, pond_id):
    if not pond_id:
        st.error("Invalid pond ID provided.")
        return []

    headers = get_auth_header(api_key)
    url = f"https://api.followupboss.com/v1/ponds/{pond_id}/people?limit=100"
    contacts = []
    next_token = None

    st.write(f"Fetching contacts for pond ID: `{pond_id}`")  # DEBUG LOG

    with st.spinner(f"Fetching contacts in pond {pond_id}..."):
        while True:
            params = {"limit": 100}
            if next_token:
                params["next"] = next_token
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Error fetching contacts by pond: {response.status_code} {response.text}")
                break
            data = response.json()
            contacts.extend(data.get("people", []))
            meta = data.get("_metadata", {})
            next_token = meta.get("next")
            if not next_token:
                break
            time.sleep(0.2)
    st.success(f"Fetched {len(contacts)} contacts from pond")
    return contacts

# ------------------------
# Streamlit App UI
# ------------------------
st.title("FUB Contacts Filter Tool")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    agents = fetch_agents(api_key)
    ponds = fetch_ponds(api_key)

    agent_names = sorted([a["name"] for a in agents if a.get("name")])
    pond_map = {p["name"]: p["id"] for p in ponds}

    st.write("Available Ponds & IDs:")
    st.write(pond_map)  # DEBUG

    filter_type = st.radio("Filter contacts by agent or pond:", ("Agent", "Pond"))

    if filter_type == "Agent":
        selected_agent = st.selectbox("Select an agent", agent_names)
        if st.button("Fetch Contacts"):
            contacts = fetch_contacts_by_agent(api_key, selected_agent)
            for contact in contacts:
                st.write(f"Name: {contact.get('name')}, assignedTo: '{selected_agent}'")

    else:
        pond_names = list(pond_map.keys())
        selected_pond = st.selectbox("Select a pond", pond_names)
        if st.button("Fetch Contacts"):
            pond_id = pond_map.get(selected_pond)
            contacts = fetch_contacts_by_pond(api_key, pond_id)
            for contact in contacts:
                st.write(f"Name: {contact.get('name')}, Pond: {selected_pond}")
