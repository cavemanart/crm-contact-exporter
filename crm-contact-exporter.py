import streamlit as st
import requests
import base64
import csv
import time

# === Config ===
CSV_FILE = "contacts_export.csv"
FUB_BASE_URL = "https://api.followupboss.com/v1"

# === API Helpers ===
def get_headers(api_key):
    return {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }

# Fetch agents
def fetch_follow_up_boss_agents(api_key):
    response = requests.get(f"{FUB_BASE_URL}/users", headers=get_headers(api_key))
    if response.status_code == 200:
        return response.json().get("users", [])
    return []

# Fetch ponds
def fetch_ponds(api_key):
    response = requests.get(f"{FUB_BASE_URL}/ponds", headers=get_headers(api_key))
    if response.status_code == 200:
        return response.json().get("ponds", [])
    return []

# Paginated fetch of all contacts
def fetch_contacts(api_key):
    all_contacts = []
    limit = 100
    offset = 0

    while True:
        response = requests.get(
            f"{FUB_BASE_URL}/people",
            headers=get_headers(api_key),
            params={"limit": limit, "offset": offset}
        )
        if response.status_code != 200:
            break

        data = response.json()
        contacts = data.get("people", [])
        if not contacts:
            break

        all_contacts.extend(contacts)
        offset += limit

        time.sleep(0.3)  # throttle slightly to avoid hitting rate limits

    return all_contacts

# Export contacts to CSV
def export_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        return

    keys = set()
    for contact in contacts:
        keys.update(contact.keys())

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sorted(keys))
        writer.writeheader()
        writer.writerows(contacts)

    st.success(f"Exported {len(contacts)} contacts to {filename}")
    with open(filename, "rb") as f:
        st.download_button("⬇️ Download CSV", f, file_name=filename, mime="text/csv")

# === Streamlit UI ===
st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    with st.spinner("Fetching agents and ponds..."):
        agents = fetch_follow_up_boss_agents(api_key)
        ponds = fetch_ponds(api_key)

    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents if a.get("email")}
    pond_map = {p["name"]: p["id"] for p in ponds}

    filter_type = st.radio("Filter contacts by:", ["Agent", "Pond", "Tag"])

    selected_option = None
    if filter_type == "Agent":
        agent_options = ["All Agents"] + list(agent_map.keys())
        selected_option = st.selectbox("Select Agent:", agent_options)

    elif filter_type == "Pond":
        if not pond_map:
            st.warning("No ponds found. Check permissions.")
        else:
            selected_option = st.selectbox("Select Pond:", list(pond_map.keys()))

    elif filter_type == "Tag":
        with st.spinner("Fetching tags from all contacts..."):
            all_contacts = fetch_contacts(api_key)
            tag_set = set()
            for c in all_contacts:
                for tag in c.get("tags", []):
                    tag_set.add(tag.strip())
            tag_options = sorted(tag_set)
        if not tag_options:
            st.warning("No tags found.")
        else:
            selected_option = st.selectbox("Select Tag:", tag_options)

    contacts_to_export = []

    if st.button("Fetch Contacts"):
        with st.spinner("Fetching contacts..."):
            all_contacts = fetch_contacts(api_key)

        if filter_type == "Agent":
            if selected_option == "All Agents":
                filtered_contacts = all_contacts
            else:
                agent_id = agent_map[selected_option]
                filtered_contacts = [
                    c for c in all_contacts if c.get("assignedTo", {}).get("id") == agent_id
                ]

        elif filter_type == "Pond":
            pond_id = pond_map.get(selected_option)
            filtered_contacts = [
                c for c in all_contacts if c.get("pond", {}).get("id") == pond_id
            ]

        elif filter_type == "Tag":
            filtered_contacts = [
                c for c in all_contacts if selected_option.strip().lower() in
                [tag.strip().lower() for tag in c.get("tags", [])]
            ]

        st.write(f"✅ Contacts matched: {len(filtered_contacts)}")
        contacts_to_export = filtered_contacts

    if contacts_to_export:
        safe_filename = selected_option.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "") if selected_option else "All"
        export_to_csv(contacts_to_export, filename=f"{filter_type}_{safe_filename}_contacts.csv")
