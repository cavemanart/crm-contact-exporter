import os
import csv
import base64
import streamlit as st
import requests
from simple_salesforce import Salesforce
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

# ----------- Helper functions -------------

def get_auth_header(api_key):
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}"}

# ----------- CRM Export Functions -------------

def get_contacts_from_followupboss(api_key, batch_size=1000):
    headers = get_auth_header(api_key)
    contacts = []
    page = 1
    total_fetched = 0

    st.info("Fetching contacts from Follow Up Boss...")
    progress = st.progress(0)

    while True:
        url = f"https://api.followupboss.com/v1/people?page={page}&limit=100"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
            break
        data = response.json()
        people = data.get('people', [])

        for idx, person in enumerate(people):
            person_id = person.get("id")
            detail_url = f"https://api.followupboss.com/v1/people/{person_id}?fields=allFields"
            detail_resp = requests.get(detail_url, headers=headers)
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                contact = {
                    "First Name": detail.get("firstName", ""),
                    "Last Name": detail.get("lastName", ""),
                    "Email": detail.get("emails", [{}])[0].get("value", "") if detail.get("emails") else "",
                    "Phone": detail.get("phones", [{}])[0].get("value", "") if detail.get("phones") else "",
                    "Tags": ", ".join(detail.get("tags", [])),
                    "Source": detail.get("source", ""),
                    "Created At": detail.get("created", ""),
                    "Address": detail.get("address", {}).get("formatted", "") if detail.get("address") else ""
                }
                contacts.append(contact)
                total_fetched += 1
                progress.progress(min(total_fetched / batch_size, 1.0))

            if total_fetched >= batch_size:
                break

        if not data.get('pagination', {}).get('nextPage') or total_fetched >= batch_size:
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
    return [
        {
            "First Name": c.properties.get("firstname", ""),
            "Last Name": c.properties.get("lastname", ""),
            "Email": c.properties.get("email", ""),
            "Phone": c.properties.get("phone", ""),
            "Created At": c.properties.get("createdate", ""),
            "Tags": "",
            "Source": "",
            "Address": ""
        } for c in all_contacts
    ]

def get_contacts_from_salesforce(username, password, security_token):
    sf = Salesforce(username=username, password=password, security_token=security_token)
    query = "SELECT FirstName, LastName, Email, Phone FROM Contact"
    results = sf.query_all(query)
    return [
        {
            "First Name": record.get("FirstName", ""),
            "Last Name": record.get("LastName", ""),
            "Email": record.get("Email", ""),
            "Phone": record.get("Phone", ""),
            "Created At": "",
            "Tags": "",
            "Source": "",
            "Address": ""
        } for record in results["records"]
    ]

# ----------- CSV Export -------------

def export_contacts_to_csv(contacts, filename):
    if not contacts:
        st.warning("No contacts to export.")
        return
    keys = contacts[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(contacts)
    st.success(f"Exported {len(contacts)} contacts to {filename}")
    with open(filename, "rb") as f:
        st.download_button(
            label="Download contacts.csv",
            data=f,
            file_name="contacts.csv",
            mime="text/csv"
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

    batch_size = st.number_input("Max Contacts to Export (batch size)", value=1000, step=100)

    if st.button("Export Contacts"):
        with st.spinner(f"Exporting contacts from {crm_choice}..."):
            if crm_choice == "Follow Up Boss":
                contacts = get_contacts_from_followupboss(creds["API Key"], batch_size)
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
