import streamlit as st
import requests
import csv
import base64
import time
from io import StringIO

def get_auth_header(api_key):
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def fetch_follow_up_boss_agents(api_key):
    headers = get_auth_header(api_key)
    url = "https://api.followupboss.com/v1/users"
    agents = []
    next_token = None

    with st.spinner("Fetching all agents..."):
        while True:
            params = {"limit": 100}
            if next_token:
                params["next"] = next_token
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Error fetching agents: {response.status_code} {response.text}")
                break
            data = response.json()
            agents.extend(data.get("users", []))
            meta = data.get("_metadata", {})
            next_token = meta.get("next")
            if not next_token:
                break
    st.success(f"Fetched {len(agents)} agents")
    return agents

def fetch_follow_up_boss_ponds(api_key):
    headers = get_auth_header(api_key)
    url = "https://api.followupboss.com/v1/ponds?limit=100"
    ponds = []
    next_token = None

    with st.spinner("Fetching all ponds..."):
        while True:
            params = {"limit": 100}
            if next_token:
                params["next"] = next_token
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Error fetching ponds: {response.status_code} {response.text}")
                break
            data = response.json()
            ponds.extend(data.get("ponds", []))
            meta = data.get("_metadata", {})
            next_token = meta.get("next")
            if not next_token:
                break
    st.success(f"Fetched {len(ponds)} ponds")
    return ponds

def fetch_contacts_by_pond(api_key, pond_id):
    headers = get_auth_header(api_key)
    url = f"https://api.followupboss.com/v1/ponds/{pond_id}/people?limit=100"
    contacts = []
    next_token = None

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

def fetch_all_contacts(api_key):
    headers = get_auth_header(api_key)
    url = "https://api.followupboss.com/v1/people?limit=100"
    contacts = []
    next_token = None

    with st.spinner("Fetching all contacts..."):
        while True:
            params = {"limit": 100}
            if next_token:
                params["next"] = next_token
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Error fetching contacts: {response.status_code} {response.text}")
                break
            data = response.json()
            contacts.extend(data.get("people", []))
            meta = data.get("_metadata", {})
            next_token = meta.get("next")
            if not next_token:
                break
            time.sleep(0.2)
    st.success(f"Fetched {len(contacts)} contacts total")
    return contacts

def export_to_csv(contacts, filename="contacts.csv"):
    if not contacts:
        st.warning("No contacts to export.")
        return

    output = StringIO()
    writer = csv.writer(output)
    headers = ["Name", "Email", "Phone", "Address", "Stage", "Assigned Agent"]
    writer.writerow(headers)

    for c in contacts:
        name = c.get("name", "")
        email = ", ".join(e["value"] for e in c.get("emails", [])) if c.get("emails") else ""
        phone = ", ".join(p["value"] for p in c.get("phones", [])) if c.get("phones") else ""
        address_obj = c.get("addresses", [])
        if address_obj and isinstance(address_obj, list) and address_obj[0]:
            addr = address_obj[0]
            address = f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}".strip(", ")
        else:
            address = ""
        stage = c.get("stage", "")
        assigned_agent = c.get("assignedTo", "")
        writer.writerow([name, email, phone, address, stage, assigned_agent])

    st.success(f"Exported {len(contacts)} contacts to {filename}")

    st.download_button(
        label="📁 Download CSV",
        data=output.getvalue(),
        file_name=filename,
        mime="text/csv",
        key="download-csv"
    )

st.title("📇 Follow Up Boss Contact Exporter with Pond Support")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    agents = fetch_follow_up_boss_agents(api_key)
    ponds = fetch_follow_up_boss_ponds(api_key)

    agent_map = {f"{a['name']} ({a['email']})": a["name"] for a in agents}
    pond_map = {p["name"]: p["id"] for p in ponds}

    options = ["All Contacts"] + list(agent_map.keys()) + list(pond_map.keys())
    selected_option = st.selectbox("Filter contacts by agent or pond:", options)

    contacts_to_export = None

    if st.button("Fetch Contacts"):
        if selected_option == "All Contacts":
            contacts_to_export = fetch_all_contacts(api_key)
        elif selected_option in agent_map:
            all_contacts = fetch_all_contacts(api_key)
            agent_name = agent_map[selected_option]
            contacts_to_export = [c for c in all_contacts if c.get("assignedTo") == agent_name]
        elif selected_option in pond_map:
            pond_id = pond_map[selected_option]
            contacts_to_export = fetch_contacts_by_pond(api_key, pond_id)
        else:
            st.error("Invalid selection")

        st.write(f"Contacts matched: {len(contacts_to_export)}")

    if contacts_to_export:
        export_to_csv(contacts_to_export, filename=f"{selected_option.replace(' ', '_')}_contacts.csv")
