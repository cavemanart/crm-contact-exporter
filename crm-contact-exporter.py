import streamlit as st
import requests
import pandas as pd
from io import BytesIO

st.title("Follow Up Boss Contact Export Tool")

# Step 1: Get API key input
api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

# Step 2: Fetch agents
@st.cache_data
def fetch_agents(api_key):
    url = "https://api.followupboss.com/v1/users"
    headers = {"Authorization": f"Bearer {api_key}"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Failed to fetch agents: {res.text}")
        return []
    users = res.json().get("users", [])
    agent_map = {user["id"]: user["email"] for user in users if user.get("role") == "Agent"}
    return agent_map

if api_key:
    agents = fetch_agents(api_key)
    agent_options = list(agents.values()) + ["Unassigned"]
    selected_agents = st.multiselect("Select Agents to Export", agent_options)

    if st.button("Export Contacts"):
        headers = {"Authorization": f"Bearer {api_key}"}
        base_url = "https://api.followupboss.com/v1/people"

        all_contacts = []
        next_url = base_url

        with st.spinner("Fetching contacts..."):
            while next_url:
                res = requests.get(next_url, headers=headers)
                if res.status_code != 200:
                    st.error(f"Error fetching contacts: {res.text}")
                    break
                data = res.json()
                all_contacts.extend(data.get("people", []))
                next_url = data.get("nextLink")

        # Step 3: Sort by selected agents
        for selected in selected_agents:
            if selected == "Unassigned":
                filtered = [p for p in all_contacts if not p.get("assignedUserId")]
                filename = "unassigned_contacts.csv"
            else:
                agent_id = next((k for k, v in agents.items() if v == selected), None)
                filtered = [p for p in all_contacts if p.get("assignedUserId") == agent_id]
                filename = f"{selected.replace('@', '_').replace('.', '_')}_contacts.csv"

            if filtered:
                df = pd.DataFrame([{
                    "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
                    "email": p.get("primaryEmail", ""),
                    "phone": p.get("primaryPhone", ""),
                    "address": p.get("address', {}).get('street', '')}",
                    "assigned_agent_id": p.get("assignedUserId", ""),
                    "stage": p.get("stage", "")
                } for p in filtered])
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Download CSV for {selected}",
                    data=csv,
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                st.info(f"No contacts found for {selected}.")
