import streamlit as st
import requests
import base64
import csv

# --- Constants ---
CSV_FILE = "contacts.csv"

# --- Helper Functions ---
def fetch_follow_up_boss_agents(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    response = requests.get("https://api.followupboss.com/v1/users", headers=headers)
    if response.status_code == 200:
        return response.json().get("users", [])
    return []

def fetch_ponds(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    response = requests.get("https://api.followupboss.com/v1/ponds", headers=headers)
    if response.status_code == 200:
        return response.json().get("ponds", [])
    return []

def fetch_contacts(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    contacts = []
    limit = 100
    offset = 0
    while True:
        response = requests.get(
            f"https://api.followupboss.com/v1/people?limit={limit}&offset={offset}",
            headers=headers,
        )
        if response.status_code != 200:
            break
        batch = response.json().get("people", [])
        contacts.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return contacts

def export_to_csv(contacts, filename=CSV_FILE):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Phone", "Tags"])
        for contact in contacts:
            name = contact.get("name", "")
            email = contact.get("emails", [{}])[0].get("value", "")
            phone = contact.get("phones", [{}])[0].get("value", "")
            tags = ", ".join(contact.get("tags", []))
            writer.writerow([name, email, phone, tags])
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📁 Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

# --- App UI ---
st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    agents = fetch_follow_up_boss_agents(api_key)
    ponds = fetch_ponds(api_key)
    all_contacts = fetch_contacts(api_key)

    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents if a.get("email")}
    pond_map = {p["name"]: p["id"] for p in ponds}

    tag_set = set()
    for c in all_contacts:
        tag_set.update(c.get("tags", []))
    tag_options = sorted(tag_set)

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
        if not tag_options:
            st.warning("No tags found in your account.")
        else:
            selected_option = st.selectbox("Select Tag:", tag_options, key="tag-filter")

    contacts_to_export = []

    if st.button("Fetch Contacts"):
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
                c for c in all_contacts if selected_option in c.get("tags", [])
            ]

        st.write(f"Contacts matched: {len(filtered_contacts)}")
        contacts_to_export = filtered_contacts

    if contacts_to_export:
        safe_filename = selected_option.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "") if selected_option else "All"
        export_to_csv(contacts_to_export, filename=f"{filter_type}_{safe_filename}_contacts.csv")
