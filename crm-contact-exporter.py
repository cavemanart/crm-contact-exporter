import streamlit as st
import requests
import csv
import base64
import time

CSV_FILE = "contacts.csv"

# 🔁 Fetch all agents using Bearer token
def fetch_follow_up_boss_agents(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
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

# 🔁 Fetch contacts, optionally filtered by agent
def fetch_follow_up_boss_contacts(access_token, limit, assigned_user_id=None):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = "https://api.followupboss.com/v1/people"
    contacts = []
    offset = 0
    with st.spinner("Fetching contacts from Follow Up Boss..."):
        while len(contacts) < limit:
            params = {"limit": 100, "offset": offset}
            if assigned_user_id:
                params["assignedUserId"] = assigned_user_id
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break
            batch = response.json().get("people", [])
            if not batch:
                break
            contacts.extend(batch)
            offset += 100
            st.progress(min(len(contacts) / limit, 1.0))
            time.sleep(0.2)
    return contacts[:limit]

# ✅ Export to CSV
def export_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        st.warning("No contacts to export.")
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        headers = ["Name", "Email", "Phone", "Address", "Assigned Agent", "Stage"]
        writer.writerow(headers)
        for c in contacts:
            name = c.get("name", "")
            email = ", ".join(e["value"] for e in c.get("emails", []))
            phone = ", ".join(p["value"] for p in c.get("phones", []))

            address_obj = c.get("addresses", [])
            if address_obj and isinstance(address_obj, list) and address_obj[0]:
                addr = address_obj[0]
                address = f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}"
            else:
                address = ""

            assigned = c.get("assignedTo")
            agent = assigned["name"] if isinstance(assigned, dict) and "name" in assigned else ""
            stage = c.get("stage", "")
            writer.writerow([name, email, phone, address, agent, stage])

    st.success(f"Exported {len(contacts)} contacts to {filename}")

    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📁 Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

# 🚀 Streamlit UI
st.title("📇 Follow Up Boss Contact Exporter")

access_token = st.text_input("Enter your Follow Up Boss Access Token", type="password")
limit = st.number_input("Number of contacts to fetch", min_value=1, max_value=5000, value=500)

if access_token:
    agents = fetch_follow_up_boss_agents(access_token)
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents}
    agent_names = ["All Agents"] + list(agent_map.keys())
    selected_agent = st.selectbox("Filter contacts by agent", agent_names)

    assigned_user_id = None if selected_agent == "All Agents" else agent_map[selected_agent]

    if st.button("Fetch and Export Contacts"):
        contacts = fetch_follow_up_boss_contacts(access_token, limit, assigned_user_id)
        export_to_csv(contacts)
