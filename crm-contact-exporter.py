import streamlit as st
import requests
import csv
import base64
import time

CSV_FILE = "contacts.csv"

# Fetch agents (users)
def fetch_follow_up_boss_agents(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode((api_key + ":").encode()).decode()
    }
    url = "https://api.followupboss.com/v1/users"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Failed to fetch agents: {response.status_code} {response.text}")
        return []
    return response.json().get("users", [])

# Fetch contacts, optionally filtered by assigned user
def fetch_follow_up_boss_contacts(api_key, limit, assigned_user_id=None):
    headers = {
        "Authorization": "Basic " + base64.b64encode((api_key + ":").encode()).decode()
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

# Export to CSV
def export_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        st.warning("No contacts to export.")
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        headers = ["Name", "Email", "Phone", "Assigned Agent", "Stage"]
        writer.writerow(headers)
        for c in contacts:
            name = c.get("name", "")
            email = ", ".join(e["value"] for e in c.get("emails", []))
            phone = ", ".join(p["value"] for p in c.get("phones", []))
            agent = c.get("assignedTo", {}).get("name", "")
            stage = c.get("stage", "")
            writer.writerow([name, email, phone, agent, stage])
    st.success(f"Exported {len(contacts)} contacts to {filename}")

    # Provide download link
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📁 Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

# Streamlit UI
st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")
limit = st.number_input("Number of contacts to fetch", min_value=1, max_value=5000, value=500)

if api_key:
    agents = fetch_follow_up_boss_agents(api_key)
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents}
    agent_names = ["All Agents"] + list(agent_map.keys())
    selected_agent = st.selectbox("Filter contacts by agent", agent_names)

    assigned_user_id = None if selected_agent == "All Agents" else agent_map[selected_agent]

    if st.button("Fetch and Export Contacts"):
        contacts = fetch_follow_up_boss_contacts(api_key, limit, assigned_user_id)
        export_to_csv(contacts)
