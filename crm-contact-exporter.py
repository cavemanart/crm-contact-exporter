import streamlit as st
import requests
import csv
import base64

# --- Constants ---
FUB_BASE_URL = "https://api.followupboss.com/v1"
CSV_FILE = "contacts_export.csv"

# --- API Headers ---
def get_headers(api_key):
    return {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }

# --- Fetch agents ---
def fetch_follow_up_boss_agents(api_key):
    url = f"{FUB_BASE_URL}/users"
    headers = get_headers(api_key)
    response = requests.get(url, headers=headers)
    return response.json().get("users", [])

# --- Fetch ponds ---
def fetch_ponds(api_key):
    url = f"{FUB_BASE_URL}/ponds"
    headers = get_headers(api_key)
    response = requests.get(url, headers=headers)
    return response.json().get("ponds", [])

# --- Fetch contacts (paginated) ---
def fetch_contacts(api_key):
    contacts = []
    headers = get_headers(api_key)
    page = 1

    while True:
        url = f"{FUB_BASE_URL}/people?page={page}&limit=100"
        response = requests.get(url, headers=headers)
        data = response.json()
        page_contacts = data.get("people", [])

        if not page_contacts:
            break

        contacts.extend(page_contacts)
        page += 1

    return contacts

# --- Export to CSV ---
def export_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        return

    fieldnames = ["Name", "Email", "Phone", "Tags", "Assigned Agent", "Pond", "Stage"]
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for c in contacts:
            writer.writerow({
                "Name": c.get("name"),
                "Email": c.get("emails", [{}])[0].get("value", ""),
                "Phone": c.get("phones", [{}])[0].get("value", ""),
                "Tags": ", ".join(c.get("tags", [])),
                "Assigned Agent": c.get("assignedTo", {}).get("name", ""),
                "Pond": c.get("pond", {}).get("name", ""),
                "Stage": c.get("stage", "")
            })

    st.success(f"✅ Exported {len(contacts)} contacts to {filename}")

# --- Streamlit App UI ---
st.title("📇 Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    with st.spinner("Fetching data..."):
        agents = fetch_follow_up_boss_agents(api_key)
        ponds = fetch_ponds(api_key)
        all_contacts = fetch_contacts(api_key)

    # Map agent and pond names
    agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents if a.get("email")}
    pond_map = {p["name"]: p["id"] for p in ponds}

    # Extract tag list
    tag_set = set()
    for c in all_contacts:
        tag_set.update(tag.strip() for tag in c.get("tags", []) if tag)

    tag_options = sorted(tag_set)

    # Filter type selection
    filter_type = st.radio("Filter contacts by:", ["Agent", "Pond", "Tag"])

    selected_option = None

    if filter_type == "Agent":
        agent_options = ["All Agents"] + list(agent_map.keys())
        selected_option = st.selectbox("Select Agent:", agent_options)

    elif filter_type == "Pond":
        if not pond_map:
            st.warning("No ponds found.")
        else:
            selected_option = st.selectbox("Select Pond:", list(pond_map.keys()))

    elif filter_type == "Tag":
        if not tag_options:
            st.warning("No tags found.")
        else:
            selected_option = st.selectbox("Select Tag:", tag_options)

    contacts_to_export = []

    if st.button("Fetch Contacts"):
        if filter_type == "Agent":
            if selected_option == "All Agents":
                filtered_contacts = all_contacts
            else:
                agent_id = agent_map[selected_option]
                filtered_contacts = [c for c in all_contacts if c.get("assignedTo", {}).get("id") == agent_id]

        elif filter_type == "Pond":
            pond_id = pond_map.get(selected_option)
            filtered_contacts = [c for c in all_contacts if c.get("pond", {}).get("id") == pond_id]

        elif filter_type == "Tag":
            filtered_contacts = [c for c in all_contacts if selected_option in c.get("tags", [])]

        st.write(f"📦 Contacts matched: {len(filtered_contacts)}")
        contacts_to_export = filtered_contacts

    if contacts_to_export:
        safe_filename = selected_option.replace(" ", "_") if selected_option else "All"
        export_to_csv(contacts_to_export, filename=f"{filter_type}_{safe_filename}_contacts.csv")
