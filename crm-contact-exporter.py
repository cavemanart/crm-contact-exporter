import streamlit as st
import requests
import csv
import base64
import time
from io import StringIO

CSV_FILE = "contacts.csv"

# Function to encode API key for Basic Auth
def get_auth_header(api_key):
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}"}

# 🔁 Fetch all agents using pagination
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

# 🔁 Fetch contacts, optionally filtered by agent, using nextLink pagination
def fetch_follow_up_boss_contacts(api_key, assigned_user_id=None):
    headers = get_auth_header(api_key)
    url = "https://api.followupboss.com/v1/people?limit=100"
    contacts = []

    with st.spinner("Fetching contacts from Follow Up Boss..."):
        while url:
            params = {}
            if assigned_user_id:
                # If filtering by agent, append param only for first call
                if "?" in url:
                    url += f"&assignedUserId={assigned_user_id}"
                else:
                    url += f"?assignedUserId={assigned_user_id}"

            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break
            data = response.json()
            batch = data.get("people", [])
            contacts.extend(batch)
            url = data.get("links", {}).get("next")  # next page link or None

            time.sleep(0.2)  # Be kind to API rate limits

    return contacts

# ✅ Export to CSV
def export_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        st.warning("No contacts to export.")
        return

    output = StringIO()
    writer = csv.writer(output)
    headers = ["Name", "Email", "Phone", "Address", "Assigned Agent", "Stage"]
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

        assigned = c.get("assignedTo")
        agent = assigned["name"] if isinstance(assigned, dict) and "name" in assigned else ""
        stage = c.get("stage", "")
        writer.writerow([name, email, phone, address, agent, stage])

    st.success(f"Exported {len(contacts)} contacts to {filename}")

    st.download_button(
        label="📁 Download CSV",
        data=output.getvalue(),
        file_name=filename,
        mime="text/csv"
    )

# 🚀 Streamlit UI
st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    agents = fetch_follow_up_boss_agents(api_key)
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents}
    agent_names = ["All Agents", "Unassigned"] + list(agent_map.keys())
    selected_agent = st.selectbox("Filter contacts by agent", agent_names)

    assigned_user_id = None
    if selected_agent == "Unassigned":
        assigned_user_id = "unassigned"  # Special handling below
    elif selected_agent != "All Agents":
        assigned_user_id = agent_map[selected_agent]

    if st.button("Fetch and Export Contacts"):
        contacts = []
        if assigned_user_id == "unassigned":
            # Fetch all contacts and filter unassigned client-side
            all_contacts = fetch_follow_up_boss_contacts(api_key)
            contacts = [c for c in all_contacts if not c.get("assignedTo")]
        elif assigned_user_id is None:
            # All agents — fetch all contacts without filter
            contacts = fetch_follow_up_boss_contacts(api_key)
        else:
            contacts = fetch_follow_up_boss_contacts(api_key, assigned_user_id)

        export_to_csv(contacts)
