import os
import csv
import streamlit as st
import requests
from simple_salesforce import Salesforce
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

# ----------- Helper functions -------------

def save_config(config):
    st.session_state['config'] = config

def load_config():
    return st.session_state.get('config', {})

# ----------- Data normalization -------------

def normalize_contact(contact):
    """
    Extract and return a dict with keys:
    First Name, Last Name, Email, Phone, Tags, Source, Created At
    Handles missing keys gracefully.
    """
    return {
        "First Name": contact.get("firstName") or contact.get("FirstName") or contact.get("first_name") or "",
        "Last Name": contact.get("lastName") or contact.get("LastName") or contact.get("last_name") or "",
        "Email": contact.get("email") or contact.get("Email") or "",
        "Phone": contact.get("phone") or contact.get("Phone") or "",
        "Tags": ",".join(contact.get("tags", [])) if isinstance(contact.get("tags"), list) else contact.get("tags", ""),
        "Source": contact.get("source") or contact.get("Source") or "",
        "Created At": contact.get("createdAt") or contact.get("CreatedAt") or contact.get("created_at") or "",
    }

# ----------- CRM Export Functions -------------

def get_contacts_from_followupboss(api_key):
    headers = {
        "Authorization": f"Basic {api_key}:"
    }
    contacts = []
    page = 1
    while True:
        url = f"https://api.followupboss.com/v1/people?page={page}&limit=100"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
            break
        data = response.json()
        contacts.extend(data.get('people', []))
        if not data.get('pagination', {}).get('nextPage'):
            break
        page += 1
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
    return [contact.to_dict() for contact in all_contacts]

def get_contacts_from_salesforce(username, password, security_token):
    sf = Salesforce(username=username, password=password, security_token=security_token)
    query = "SELECT Id, FirstName, LastName, Email, Phone FROM Contact"
    results = sf.query_all(query)
    return results['records']

# ----------- CSV Export -------------

def export_contacts_to_csv(contacts, filename):
    if not contacts:
        st.warning("No contacts to export.")
        return

    normalized_contacts = [normalize_contact(c) for c in contacts]

    fieldnames = ["First Name", "Last Name", "Email", "Phone", "Tags", "Source", "Created At"]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_contacts)

    st.success(f"Exported {len(normalized_contacts)} contacts to {filename}")
    with open(filename, 'rb') as f:
        st.download_button(
            label="Download contacts.csv",
            data=f,
            file_name=filename,
            mime='text/csv'
        )

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
        creds[field] = st.text_input(f"{field}", type="password" if "key" in field.lower() or "password" in field.lower() else "default")

    if st.button("Export Contacts"):
        with st.spinner(f"Exporting contacts from {crm_choice}..."):
            if crm_choice == "Follow Up Boss":
                contacts = get_contacts_from_followupboss(creds["API Key"])
            elif crm_choice == "HubSpot":
                contacts = get_contacts_from_hubspot(creds["API Key"])
            elif crm_choice == "Salesforce":
                contacts = get_contacts_from_salesforce(creds["Username"], creds["Password"], creds["Security Token"])
            else:
                st.error("Unsupported CRM selected.")
                return

            export_contacts_to_csv(contacts, "contacts.csv")

if __name__ == "__main__":
    main()
