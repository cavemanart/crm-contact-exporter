import streamlit as st
import requests
import csv
from io import StringIO

st.title("Follow Up Boss Contact Export Tool")

# User input
api_key = st.text_input("Enter your Follow Up Boss API Key:", type="password")
limit = st.number_input("Number of contacts to fetch:", min_value=1, max_value=10000, value=1000)
assigned_user_id = st.text_input("Assigned User ID (optional):")

def fetch_follow_up_boss_contacts(api_key, limit, assigned_user_id=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    contacts = []
    offset = None

    while True:
        params = {"limit": 100}
        if assigned_user_id:
            params["assignedUserId"] = assigned_user_id
        if offset:
            params["offset"] = offset

        response = requests.get("https://api.followupboss.com/v1/people", headers=headers, params=params)
        if response.status_code != 200:
            st.error(f"Failed to fetch contacts: {response.text}")
            break

        data = response.json()
        if not data.get("people"):
            break

        contacts.extend(data["people"])
        if len(contacts) >= limit:
            break

        offset = data.get("next")

        if not offset:
            break

    return contacts[:limit]

def export_to_csv(contacts, filename="contacts.csv"):
    if not contacts:
        st.warning("No contacts found to export.")
        return

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Phone", "Address", "Assigned Agent", "Stage"])

    for c in contacts:
        name = c.get("name", "")
        email = c["emails"][0]["value"] if c.get("emails") else ""
        phone = c["phones"][0]["value"] if c.get("phones") else ""
        address = c["addresses"][0]["street"] if c.get("addresses") else ""
        assigned_agent = c.get("assignedTo", {}).get("name", "Unassigned")
        stage = c.get("stage", "")

        writer.writerow([name, email, phone, address, assigned_agent, stage])

    st.download_button(
        label=f"Download {filename}",
        data=output.getvalue(),
        file_name=filename,
        mime="text/csv"
    )

if st.button("Fetch and Export Contacts"):
    contacts = fetch_follow_up_boss_contacts(api_key, limit, assigned_user_id)

    if assigned_user_id:
        export_to_csv(contacts)
    else:
        # Group all contacts by agent name or "Unassigned"
        grouped_contacts = {}
        for c in contacts:
            assigned = c.get("assignedTo")
            agent_name = assigned["name"] if isinstance(assigned, dict) and "name" in assigned else "Unassigned"
            grouped_contacts.setdefault(agent_name, []).append(c)

        for agent_name, agent_contacts in grouped_contacts.items():
            safe_name = agent_name.replace(" ", "_").replace("@", "_").replace(".", "_").lower()
            filename = f"{safe_name}_contacts.csv"
            export_to_csv(agent_contacts, filename)
