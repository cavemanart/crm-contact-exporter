import streamlit as st
import requests
import base64
import csv

CSV_FILE = "contacts.csv"

# Function to fetch all contacts using pagination
def fetch_all_contacts(api_key):
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
    }
    all_contacts = []
    page = 1
    while True:
        url = f"https://api.followupboss.com/v1/people?page={page}&limit=100"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"Error fetching contacts: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        all_contacts.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_contacts

# UI Inputs
st.title("Follow Up Boss Contact Export")
api_key = st.text_input("Enter your FUB API Key", type="password")
filter_type = st.radio("Filter contacts by:", ["Agent", "Pond", "Tag"])

# Fetch all contacts and extract filters
if api_key:
    all_contacts = fetch_all_contacts(api_key)

    agent_ids = sorted({c.get("assignedTo", {}).get("id") for c in all_contacts if c.get("assignedTo")})
    pond_ids = sorted({c.get("pond", {}).get("id") for c in all_contacts if c.get("pond")})
    tag_set = set()
    for c in all_contacts:
        tag_set.update(c.get("tags", []))
    tag_options = sorted(tag_set)

    selected_option = None

    if filter_type == "Agent":
        selected_option = st.selectbox("Select Agent ID:", agent_ids)
    elif filter_type == "Pond":
        selected_option = st.selectbox("Select Pond ID:", pond_ids)
    elif filter_type == "Tag":
        if not tag_options:
            st.warning("No tags found.")
        else:
            selected_option = st.selectbox("Select Tag:", tag_options)

    if st.button("Fetch Contacts"):
        filtered_contacts = []

        if filter_type == "Agent":
            filtered_contacts = [c for c in all_contacts if c.get("assignedTo", {}).get("id") == selected_option]
        elif filter_type == "Pond":
            filtered_contacts = [c for c in all_contacts if c.get("pond", {}).get("id") == selected_option]
        elif filter_type == "Tag":
            filtered_contacts = [c for c in all_contacts if selected_option in c.get("tags", [])]

        if not filtered_contacts:
            st.warning("No contacts found with selected filter.")
        else:
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Name", "Email", "Phone", "Tags"])
                for contact in filtered_contacts:
                    name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip()
                    email = contact.get("emails", [{}])[0].get("value", "")
                    phone = contact.get("phones", [{}])[0].get("value", "")
                    tags = ", ".join(contact.get("tags", []))
                    writer.writerow([name, email, phone, tags])
            st.success(f"Exported {len(filtered_contacts)} contacts to {CSV_FILE}")
