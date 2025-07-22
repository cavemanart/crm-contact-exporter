import streamlit as st
import requests
import csv
import os
from io import StringIO

st.set_page_config(page_title="FUB Contact Exporter", layout="wide")

st.title("Follow Up Boss Contact Exporter")

# Input: API Key
api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Function to fetch agents
@st.cache_data
def get_agents():
    url = "https://api.followupboss.com/v1/users"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        st.error(f"Failed to fetch agents: {resp.status_code}")
        return []
    data = resp.json()
    agents = [{"name": user["name"], "id": user["id"], "email": user["email"]} for user in data["users"]]
    return agents

# Function to fetch all contacts (paginated)
def fetch_contacts():
    all_contacts = []
    url = "https://api.followupboss.com/v1/people"
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            st.error(f"Follow Up Boss API error: {res.status_code} {res.text}")
            return []
        data = res.json()
        all_contacts.extend(data["people"])
        url = data.get("next", None)
    return all_contacts

# UI: Agent selection
agents = get_agents()
agent_options = ["Unassigned"] + [f'{a["name"]} ({a["email"]})' for a in agents]
selected_agents = st.multiselect("Select agents to export", agent_options)

if st.button("Export Contacts"):
    all_contacts = fetch_contacts()
    if not all_contacts:
        st.warning("No contacts found.")
    for selected_agent in selected_agents:
        if selected_agent == "Unassigned":
            filtered = [p for p in all_contacts if p.get("assignedTo") is None]
            filename = "unassigned_contacts.csv"
        else:
            agent = next((a for a in agents if f'{a["name"]} ({a["email"]})' == selected_agent), None)
            if not agent:
                continue
            filtered = [p for p in all_contacts if p.get("assignedTo", {}).get("id") == agent["id"]]
            filename = f"{agent['name'].replace(' ', '_')}_contacts.csv"

        if not filtered:
            st.info(f"No contacts found for {selected_agent}.")
            continue

        # Write CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "Phone", "Address", "Stage", "Assigned Agent Email", "Original Agent ID"])
        for p in filtered:
            name = p.get("name", "")
            email = p.get("emails")[0]["value"] if p.get("emails") else ""
            phone = p.get("phones")[0]["value"] if p.get("phones") else ""
            address = p.get("addresses")[0]["fullAddress"] if p.get("addresses") else ""
            stage = p.get("stage", "")
            assigned_email = p.get("assignedTo", {}).get("email", "") if p.get("assignedTo") else ""
            original_agent_id = p.get("assignedTo", {}).get("id", "") if p.get("assignedTo") else ""
            writer.writerow([name, email, phone, address, stage, assigned_email, original_agent_id])

        # Download link
        st.download_button(
            label=f"Download {filename}",
            data=output.getvalue(),
            file_name=filename,
            mime="text/csv"
        )
