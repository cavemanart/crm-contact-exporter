import streamlit as st
import requests
import csv
import base64
import time

CSV_FILE = "contacts.csv"

# --- Fetch all contacts with pagination ---
def fetch_contacts(api_key, limit=100):
    contacts = []
    offset = 0

    while True:
        url = f"https://api.followupboss.com/v1/people?limit={limit}&offset={offset}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"Error fetching contacts: {response.status_code}")
            break

        data = response.json()
        batch = data.get("people", [])
        contacts.extend(batch)

        if len(batch) < limit:
            break

        offset += limit
        time.sleep(0.5)  # to avoid rate limits

    return contacts

# --- Filter contacts by tag ---
def filter_contacts_by_tag(contacts, tag_name="BRIGHTONPOND"):
    filtered = []
    for c in contacts:
        tags = c.get("tags", [])
        if any(tag.get("name", "").upper() == tag_name.upper() for tag in tags):
            filtered.append(c)
    return filtered

# --- Convert contacts to CSV ---
def write_contacts_to_csv(contacts, filename=CSV_FILE):
    if not contacts:
        return

    fieldnames = ["name", "email", "phone", "stage", "source", "assignedTo", "tags"]
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for c in contacts:
            writer.writerow({
                "name": c.get("name"),
                "email": c.get("emails", [{}])[0].get("value"),
                "phone": c.get("phones", [{}])[0].get("value"),
                "stage": c.get("stage"),
                "source": c.get("source"),
                "assignedTo": c.get("assignedTo", {}).get("name"),
                "tags": ", ".join([tag.get("name", "") for tag in c.get("tags", [])])
            })

# --- Streamlit UI ---
st.title("🏷️ Export Contacts with Tag: BRIGHTONPOND")

api_key = st.text_input("Enter Follow Up Boss API Key", type="password")
limit = st.number_input("Contacts per batch", min_value=100, max_value=500, value=100)

if st.button("Fetch & Export"):
    if not api_key:
        st.warning("API key is required.")
    else:
        with st.spinner("Fetching contacts..."):
            all_contacts = fetch_contacts(api_key, limit=limit)
            brighton_contacts = filter_contacts_by_tag(all_contacts, tag_name="BRIGHTONPOND")
            write_contacts_to_csv(brighton_contacts)

        if brighton_contacts:
            st.success(f"Exported {len(brighton_contacts)} contacts with tag 'BRIGHTONPOND'.")
            with open(CSV_FILE, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="{CSV_FILE}">📥 Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("No contacts found with the 'BRIGHTONPOND' tag.")
