import streamlit as st
import requests
import base64
import csv

st.set_page_config(page_title="FUB Contact Exporter", layout="centered")
st.title("📇 Follow Up Boss Contact Exporter")

# --- Utils ---
def get_headers(api_key):
    return {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }

def fetch_agents(api_key):
    url = "https://api.followupboss.com/v1/users"
    res = requests.get(url, headers=get_headers(api_key))
    if res.status_code == 200:
        return res.json().get("users", [])
    return []

def fetch_ponds(api_key):
    url = "https://api.followupboss.com/v1/ponds"
    res = requests.get(url, headers=get_headers(api_key))
    if res.status_code == 200:
        return res.json().get("ponds", [])
    return []

def fetch_tags(api_key):
    url = "https://api.followupboss.com/v1/tags"
    res = requests.get(url, headers=get_headers(api_key))
    if res.status_code == 200:
        return sorted(res.json().get("tags", []))
    return []

def fetch_all_contacts(api_key):
    contacts = []
    url = "https://api.followupboss.com/v1/people"
    headers = get_headers(api_key)
    page = 1

    while True:
        res = requests.get(url, headers=headers, params={"limit": 100, "page": page})
        if res.status_code != 200:
            break
        data = res.json()
        batch = data.get("people", [])
        contacts.extend(batch)
        if not data.get("more"):
            break
        page += 1

    return contacts

def export_to_csv(contacts, filename="contacts.csv"):
    if not contacts:
        st.warning("No contacts to export.")
        return

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Phone", "Tags", "Stage", "Assigned Agent", "Pond", "Street", "City", "State", "Zip"])

        for c in contacts:
            writer.writerow([
                c.get("name"),
                c.get("emails", [{}])[0].get("value", ""),
                c.get("phones", [{}])[0].get("value", ""),
                ", ".join(c.get("tags", [])),
                c.get("stage", ""),
                c.get("assignedTo", {}).get("name", ""),
                c.get("pond", {}).get("name", ""),
                c.get("addresses", [{}])[0].get("street", ""),
                c.get("addresses", [{}])[0].get("city", ""),
                c.get("addresses", [{}])[0].get("state", ""),
                c.get("addresses", [{}])[0].get("zip", "")
            ])

    with open(filename, "rb") as file:
        btn = st.download_button(
            label="📁 Download CSV",
            data=file,
            file_name=filename,
            mime="text/csv"
        )

# --- App UI ---
api_key = st.text_input("🔑 Enter your Follow Up Boss API Key", type="password")

if api_key:
    filter_type = st.radio("🔍 Filter contacts by:", ["Agent", "Pond", "Tag"])

    if filter_type == "Agent":
        agents = fetch_agents(api_key)
        agent_map = {f"{a['name']} ({a['email']})": a["id"] for a in agents if a.get("email")}
        agent_option = st.selectbox("Select Agent:", ["All Agents"] + list(agent_map.keys()))
    elif filter_type == "Pond":
        ponds = fetch_ponds(api_key)
        pond_map = {p["name"]: p["id"] for p in ponds}
        pond_option = st.selectbox("Select Pond:", list(pond_map.keys()))
    elif filter_type == "Tag":
        tag_options = fetch_tags(api_key)
        tag_option = st.selectbox("Select Tag:", tag_options)

    if st.button("🚀 Fetch Contacts"):
        st.info("Fetching contacts, please wait...")

        contacts = fetch_all_contacts(api_key)

        if filter_type == "Agent":
            if agent_option == "All Agents":
                filtered = contacts
            else:
                agent_id = agent_map[agent_option]
                filtered = [c for c in contacts if c.get("assignedTo", {}).get("id") == agent_id]

        elif filter_type == "P
