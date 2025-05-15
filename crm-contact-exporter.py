import base64
import csv
import streamlit as st
import requests
from simple_salesforce import Salesforce
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException
from io import StringIO

# ----------- Helper functions -------------

def save_config(config):
    st.session_state['config'] = config

def load_config():
    return st.session_state.get('config', {})

# ----------- Follow Up Boss Helpers -------------

def safe_get_first_email(contact):
    emails = contact.get("emails")
    if emails and isinstance(emails, list) and len(emails) > 0:
        return emails[0].get("email", "")
    return ""

def safe_get_first_phone(contact):
    phones = contact.get("phones")
    if phones and isinstance(phones, list) and len(phones) > 0:
        return phones[0].get("phone", "")
    return ""

def safe_get_first_address(contact):
    addresses = contact.get("addresses")
    if addresses and isinstance(addresses, list) and len(addresses) > 0:
        addr = addresses[0]
        parts = [
            addr.get("street1", ""),
            addr.get("street2", ""),
            addr.get("city", ""),
            addr.get("state", ""),
            addr.get("zip", ""),
            addr.get("country", "")
        ]
        return ", ".join([p for p in parts if p])
    return ""

# ----------- CRM Export Functions -------------

def get_contacts_from_followupboss(api_key):
    # Use Basic Auth with API key as username, blank password
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    headers = {
        "Authorization": f"Basic {token}"
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

def export_contacts_to_csv(contacts):
    if not contacts:
        st.warning("No contacts to export.")
        return None

    # Define the CSV headers exactly as requested
    fieldnames = ["First Name", "Last Name", "Email", "Phone", "Address", "Tags", "Source", "Created At"]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for contact in contacts:
        row = {
            "First Name": contact.get("firstName", ""),
            "Last Name": contact.get("lastName", ""),
            "Email": safe_get_first_email(contact),
            "Phone": safe_get_first_phone(contact),
            "Address": safe_get_first_address(contact),
            "Tags": ", ".join(contact.get("tags", [])) if contact.get("tags") else "",
            "Source": contact.get("source", ""),
            "Created At": contact.get("createdAt", "")
        }
        writer.writerow(row)

    return output.getvalue()

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
            contacts = []
            if crm_choice == "Follow Up Boss":
                contacts = get_contacts_from_followupboss(creds["API Key"])
            elif crm_choice == "HubSpot":
                contacts = get_contacts_from_hubspot(creds["API Key"])
            elif crm_choice == "Salesforce":
                contacts = get_contacts_from_salesforce(creds["Username"], creds["Password"], creds["Security Token"])
            else:
                st.error("Unsupported CRM selected.")
                return

            csv_content = export_contacts_to_csv(contacts)
            if csv_content:
                st.success(f"Exported {len(contacts)} contacts!")

                st.download_button(
                    label="Download contacts.csv",
                    data=csv_content,
                    file_name="contacts.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
