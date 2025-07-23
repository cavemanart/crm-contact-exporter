pimport streamlit as st
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
            return []0
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
            writer.wrimport streamlit as st
import requests
import csv
import base64

# --- Constants ---
CONTACTS_API_URL = "https://api.followupboss.com/v1/people"
PONDS_API_URL = "https://api.followupboss.com/v1/ponds"
AGENTS_API_URL = "https://api.followupboss.com/v1/users"

# --- Helper Functions ---
def fetch_follow_up_boss_agents(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    response = requests.get(AGENTS_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def fetch_ponds(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    response = requests.get(PONDS_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def fetch_contacts(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    contacts = []
    page = 1
    per_page = 100
    while True:
        response = requests.get(f"{CONTACTS_API_URL}?page={page}&limit={per_page}", headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        contacts.extend(data)
        if len(data) < per_page:
            break
        page += 1
    return contacts

def export_to_csv(contacts, filename="exported_contacts.csv"):
    if not contacts:
        return
    keys = ["id", "name", "email", "phone", "tags"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for c in contacts:
            writer.writerow({
                "id": c.get("id"),
                "name": c.get("name"),
                "email": c.get("emails")[0]["value"] if c.get("emails") else "",
                "phone": c.get("phones")[0]["value"] if c.get("phones") else "",
                "tags": ", ".join(c.get("tags", [])),
            })
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
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

    # Extract unique tags from all contacts
    tag_set = set()
    for c in all_contacts:
        tag_set.update(c.get("tags", []))
    tag_options = sorted(tag_set)

    # --- Filter UI ---
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
            export_to_csv(contacts_to_export, filename=f"{filter_type}_{safe_filename}_contacts.csv")iterow([name, email, phone, assigned_agent, pond, tags, street, city, state, zip_code])

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
