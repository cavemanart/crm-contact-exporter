import streamlit as st
import requests
import csv
import base64
import time

CSV_FILE = "contacts.csv"

# 🔁 Fetch all agents using pagination
def fetch_follow_up_boss_agents(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    url = "https://api.followupboss.com/v1/users?limit=100"
    agents = []
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            st.error(f"Failed to fetch agents: {res.text}")
            return []
        data = res.json()
        agents.extend(data.get("users", []))
        url = data.get("next", None)
    return agents

# 📩 Fetch all contacts
def fetch_follow_up_boss_contacts(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    url = "https://api.followupboss.com/v1/people?limit=100"
    contacts = []
    while url:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            st.error(f"Failed to fetch contacts: {res.text}")
            return []
        data = res.json()
        contacts.extend(data.get("people", []))
        url = data.get("next", None)
    return contacts

# 💾 Save contacts to CSV
def save_contacts_to_csv(contacts, filename=CSV_FILE):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Phone", "Assigned Agent", "Pond", "Tags", "Street", "City", "State", "Zip"])
        for contact in contacts:
            name = contact.get("name", "")
            email = contact.get("emails", [{}])[0].get("value", "")
            phone = contact.get("phones", [{}])[0].get("value", "")
            assigned_agent = contact.get("assignedTo", {}).get("name", "")
            pond = contact.get("pond", {}).get("name", "")
            tags = ", ".join(contact.get("tags", []))
            address = contact.get("address", {})
            street = address.get("street", "")
            city = address.get("city", "")
            state = address.get("state", "")
            zip_code = address.get("zipCode", "")
            writer.writerow([name, email, phone, assigned_agent, pond, tags, street, city, state, zip_code])

# 🚀 Streamlit App
st.title("Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    filter_type = st.radio("Filter contacts by:", ["Agent", "Pond", "Tag"])

    all_contacts = fetch_follow_up_boss_contacts(api_key)

    if filter_type == "Agent":
        agents = fetch_follow_up_boss_agents(api_key)
        agent_names = [a["name"] for a in agents]
        selected_option = st.selectbox("Select Agent:", agent_names)

    elif filter_type == "Pond":
        pond_names = sorted(set(c.get("pond", {}).get("name", "") for c in all_contacts if c.get("pond")))
        selected_option = st.selectbox("Select Pond:", pond_names)

    elif filter_type == "Tag":
        tag_input = st.text_input("Enter tag keyword (e.g. BRIGHTONPOOL):").strip().lower()
        tag_set = set()
        for c in all_contacts:
            tags = c.get("tags", [])
            tag_set.update(tags)
        matching_tags = sorted([t for t in tag_set if tag_input in t.lower()])
        if matching_tags:
            selected_option = st.selectbox("Matching Tags:", matching_tags)
        else:
            st.warning("No matching tags found.")
            selected_option = None

    if st.button("Fetch Contacts"):
        if filter_type == "Agent":
            filtered_contacts = [
                c for c in all_contacts
                if c.get("assignedTo", {}).get("name", "") == selected_option
            ]
        elif filter_type == "Pond":
            filtered_contacts = [
                c for c in all_contacts
                if c.get("pond", {}).get("name", "") == selected_option
            ]
        elif filter_type == "Tag" and selected_option:
            filtered_contacts = [
                c for c in all_contacts
                if selected_option in c.get("tags", [])
            ]
        else:
            filtered_contacts = []

        st.success(f"Found {len(filtered_contacts)} contacts.")
        if filtered_contacts:
            save_contacts_to_csv(filtered_contacts)
            with open(CSV_FILE, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="{CSV_FILE}">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
