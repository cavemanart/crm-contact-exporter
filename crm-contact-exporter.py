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

def fetch_follow_up_boss_contacts(api_key):
    headers = get_auth_header(api_key)
    url = "https://api.followupboss.com/v1/people?limit=100"
    contacts = []

    with st.spinner("Fetching all contacts from Follow Up Boss..."):
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break
            data = response.json()
            contacts.extend(data.get("people", []))
            url = data.get("links", {}).get("next")
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
        assigned = c.get("assignedTo")
        assigned_agent = assigned.get("name", "") if isinstance(assigned, dict) else ""
        writer.writerow([name, email, phone, address, stage, assigned_agent])

    st.success(f"Exported {len(contacts)} contacts to {filename}")

    st.download_button(
        label="📁 Download CSV",
        data=output.getvalue(),
        file_name=filename,
        mime="text/csv",
        key="download-csv"
    )

st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    agents = fetch_follow_up_boss_agents(api_key)
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents}

    options = ["All Agents", "Brighton Office Pond"] + list(agent_map.keys())
    selected_option = st.selectbox("Filter contacts by:", options)

    contacts_to_export = None

    # Debug button to inspect assignedTo fields of first 20 contacts
    if st.button("Debug AssignedTo Fields"):
        all_contacts = fetch_follow_up_boss_contacts(api_key)
        for i, c in enumerate(all_contacts[:20]):
            st.write(f"{i+1}. Name: {c.get('name')}, assignedTo: {repr(c.get('assignedTo'))}")

    if st.button("Fetch Contacts"):
        all_contacts = fetch_follow_up_boss_contacts(api_key)

        def is_unassigned(contact):
            assigned = contact.get("assignedTo")
            return assigned is None or assigned == {} or assigned == ""

        if selected_option == "All Agents":
            filtered_contacts = all_contacts
        elif selected_option == "Brighton Office Pond":
            filtered_contacts = [c for c in all_contacts if is_unassigned(c)]
        else:
            agent_id = agent_map[selected_option]
            filtered_contacts = [c for c in all_contacts if c.get("assignedTo", {}).get("id") == agent_id]

        st.write(f"Contacts matched: {len(filtered_contacts)}")
        contacts_to_export = filtered_contacts

    if contacts_to_export:
        export_to_csv(contacts_to_export, filename=f"{selected_option.replace(' ', '_')}_contacts.csv")
