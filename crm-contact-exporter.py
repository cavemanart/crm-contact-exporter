import streamlit as st
import requests
import csv
from io import StringIO

st.title("Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

@st.cache_data
def get_agents():
    url = "https://api.followupboss.com/v1/users"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Failed to fetch agents: {res.text}")
        return []
    users = res.json().get("users", [])
    return users

def fetch_all_contacts():
    contacts = []
    url = "https://api.followupboss.com/v1/people?limit=100"
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            st.error(f"Follow Up Boss API error: {res.status_code} {res.text}")
            return contacts
        data = res.json()
        contacts.extend(data.get("people", []))
        url = data.get("links", {}).get("next")
    return contacts

if api_key:
    agents = get_agents()
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents}
    agent_map["Unassigned"] = None

    selected_agents = st.multiselect("Select agents to export", list(agent_map.keys()))

    if st.button("Export Contacts"):
        all_contacts = fetch_all_contacts()
        if not all_contacts:
            st.warning("No contacts fetched.")
        for selected in selected_agents:
            if selected == "Unassigned":
                filtered = [c for c in all_contacts if not c.get("assignedTo")]
                filename = "unassigned_contacts.csv"
            else:
                agent_id = agent_map[selected]
                filtered = [c for c in all_contacts if c.get("assignedTo", {}).get("id") == agent_id]
                filename = f"{selected.replace('@','_').replace(' ','_').replace('.','_')}_contacts.csv"

            if not filtered:
                st.info(f"No contacts for {selected}")
                continue

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Name", "Email", "Phone", "Address", "Stage", "Assigned Agent Email", "Assigned Agent ID"])
            for c in filtered:
                name = c.get("name", "")
                email = c.get("emails")[0]["value"] if c.get("emails") else ""
                phone = c.get("phones")[0]["value"] if c.get("phones") else ""
                address = c.get("addresses")[0]["fullAddress"] if c.get("addresses") else ""
                stage = c.get("stage", "")
                assigned_email = c.get("assignedTo", {}).get("email", "") if c.get("assignedTo") else ""
                assigned_id = c.get("assignedTo", {}).get("id", "") if c.get("assignedTo") else ""
                writer.writerow([name, email, phone, address, stage, assigned_email, assigned_id])

            st.download_button(
                label=f"Download CSV for {selected}",
                data=output.getvalue(),
                file_name=filename,
                mime="text/csv"
            )
