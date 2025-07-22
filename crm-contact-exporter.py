import streamlit as st
import requests
import csv
from io import StringIO

# -------------------------------
# CONFIGURATION
# -------------------------------
FUB_API_KEY = st.secrets["FUB_API_KEY"]
BASE_URL = "https://api.followupboss.com/v1"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Basic {FUB_API_KEY}"
}

# -------------------------------
# FUNCTIONS
# -------------------------------
def get_agents():
    response = requests.get(f"{BASE_URL}/users", headers=HEADERS)
    agents = response.json()
    return agents["users"]

def get_contacts_by_agent(agent_id=None):
    page = 1
    per_page = 100
    all_contacts = []

    while True:
        params = {"page": page, "limit": per_page}
        if agent_id != "unassigned":
            params["assignedUserId"] = agent_id
        response = requests.get(f"{BASE_URL}/people", headers=HEADERS, params=params)
        if response.status_code != 200:
            break
        contacts = response.json()["people"]

        # Filter unassigned if needed
        if agent_id == "unassigned":
            contacts = [c for c in contacts if not c.get("assignedUserId")]

        all_contacts.extend(contacts)
        if len(contacts) < per_page:
            break
        page += 1
    return all_contacts

def export_contacts_to_csv(contacts, filename):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone", "Address", "Assigned Agent", "Stage"])

    for contact in contacts:
        name = contact.get("name", "")
        email = contact["emails"][0]["value"] if contact.get("emails") else ""
        phone = contact["phones"][0]["value"] if contact.get("phones") else ""
        address = contact.get("primaryAddress", {}).get("street", "")
        agent = contact.get("assignedUser", {}).get("name", "Unassigned")
        stage = contact.get("stage", "")
        writer.writerow([name, email, phone, address, agent, stage])

    st.download_button(
        label="Download CSV",
        data=output.getvalue(),
        file_name=filename,
        mime="text/csv"
    )

# -------------------------------
# UI
# -------------------------------
st.title("FUB Contact Export Tool")

agents = get_agents()
agent_map = {agent["name"]: agent["id"] for agent in agents}
agent_names = list(agent_map.keys())
agent_names.insert(0, "Unassigned")  # Add this line to include Unassigned

selected_agent = st.selectbox("Select an Agent (or Unassigned)", agent_names)

if st.button("Fetch and Export Contacts"):
    with st.spinner("Fetching contacts..."):
        agent_id = agent_map.get(selected_agent, "unassigned")
        contacts = get_contacts_by_agent(agent_id)
        export_contacts_to_csv(contacts, f"{selected_agent.replace(' ', '_')}_contacts.csv")
