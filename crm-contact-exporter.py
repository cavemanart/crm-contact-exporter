import os
import csv
import json
import streamlit as st
import requests
from simple_salesforce import Salesforce
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

PROGRESS_FILE = "progress.json"
CSV_FILE = "contacts_export.csv"

# ----------- Helper Functions -------------

def save_progress(progress_data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def reset_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

def export_contacts_to_csv(contacts, append=True):
    if not contacts:
        st.warning("No contacts to export.")
        return

    # Define the exact desired headers
    headers = ["First Name", "Last Name", "Email", "Phone", "Address", "Tags", "Source", "Created At"]

    # Format contacts
    formatted = []
    for c in contacts:
        formatted.append({
            "First Name": c.get("firstName", ""),
            "Last Name": c.get("lastName", ""),
            "Email": c.get("emails", [{}])[0].get("value", "") if c.get("emails") else "",
            "Phone": c.get("phones", [{}])[0].get("value", "") if c.get("phones") else "",
            "Address": c.get("primaryAddress", {}).get("street", ""),
            "Tags": ", ".join(c.get("tags", [])),
            "Source": c.get("source", ""),
            "Created At": c.get("createdAt", "")
        })

    mode = 'a' if append and os.path.exists(CSV_FILE) else 'w'
    with open(CSV_FILE, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if mode == 'w':
            writer.writeheader()
        writer.writerows(formatted)

# ----------- CRM API Functions -------------

def get_followupboss_contacts(api_key, start_page=1):
    headers = {
        "Authorization": f"Basic {api_key}:".encode("ascii").decode("utf-8")
    }
    contacts = []
    page = start_page
    has_next = True
    batch_size = 100

    with st.spinner("Fetching contacts..."):
        progress = st.progress(0)
        count = 0
        while has_next:
            url = f"https://api.followupboss.com/v1/people?page={page}&limit={batch_size}"
            response = requests.get(url, headers={
                "Authorization": f"Basic {requests.auth._basic_auth_str(api_key, '')}"
            })

            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break

            data = response.json()
            batch = data.get("people", [])
            contacts.extend(batch)
            export_contacts_to_csv(batch)

            page += 1
            count += len(batch)
            save_progress({"page": page})
            has_next = data.get("pagination", {}).get("nextPage", False)

            progress.progress(min(1.0, count / 13000))  # assuming 13k max

    return contacts

def get_contacts_from_hubspot(api_key):
    client = HubSpot(api_key=api_key)
    all_contacts = []
    after = None
    while True:
        try:
            if after:
                page = client.crm.contacts.basic_api.get_page(limit=100, after=after)
            else:
                page = client.crm.contacts.basic_api.get_page(limit=100)
            all_contacts.extend(page.results)
            after = page.paging.next.after if page.paging else None
            if not after:
                break
        except ApiException as e:
            st.error(f"HubSpot API error: {e}")
            break
    export_contacts_to_csv([c.to_dict() for c in all_contacts])

def get_contacts_from_salesforce(username, password, security_token):
    sf = Salesforce(username=username, password=password, security_token=security_token)
    query = "SELECT FirstName, LastName, Email, Phone FROM Contact"
    records = sf.query_all(query)['records']
    formatted = [{
        "First Name": r.get("FirstName"),
        "Last Name": r.get("LastName"),
        "Email": r.get("Email"),
        "Phone": r.get("Phone"),
        "Address": "",
        "Tags": "",
        "Source": "",
        "Created At": ""
    } for r in records]
    export_contacts_to_csv(formatted)

# ----------- Streamlit UI -------------

def main():
    st.title("CRM Contact Exporter")

    presets = {
        "Follow Up Boss": ["API Key"],
        "HubSpot": ["API Key"],
        "Salesforce": ["Username", "Password", "Security Token"]
    }

    crm_choice = st.selectbox("Select CRM", list(presets.keys()))

    creds = {}
    for field in presets[crm_choice]:
        creds[field] = st.text_input(field, type="password" if "key" in field.lower() or "password" in field.lower() else "default")

    progress_state = load_progress()
    resume = False
    if crm_choice == "Follow Up Boss" and progress_state.get("page"):
        resume = st.checkbox(f"Resume from page {progress_state['page']}?", value=True)

    if st.button("Start Export"):
        reset_csv = st.checkbox("Start fresh (delete previous progress)?")
        if reset_csv:
            reset_progress()

        if crm_choice == "Follow Up Boss":
            page = progress_state.get("page", 1) if resume else 1
            get_followupboss_contacts(creds["API Key"], start_page=page)
        elif crm_choice == "HubSpot":
            get_contacts_from_hubspot(creds["API Key"])
        elif crm_choice == "Salesforce":
            get_contacts_from_salesforce(creds["Username"], creds["Password"], creds["Security Token"])

        st.success("Contacts export complete.")
        with open(CSV_FILE, "rb") as f:
            st.download_button("Download CSV", f, file_name="contacts_export.csv", mime="text/csv")

if __name__ == "__main__":
    main()
