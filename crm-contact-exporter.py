import os
import csv
import json
import streamlit as st
import requests
from simple_salesforce import Salesforce
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

CHECKPOINT_FILE = "last_fub_id.txt"

def save_last_id(contact_id):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(contact_id))

def load_last_id():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return f.read().strip()
    return None

def get_contacts_from_followupboss(api_key, batch_size=1000):
    headers = {"Authorization": f"Basic {api_key}:"}
    contacts = []
    page = 1
    total_fetched = 0
    last_processed_id = load_last_id()

    with st.spinner("Fetching contacts..."):
        progress = st.progress(0)
        while True:
            url = f"https://api.followupboss.com/v1/people?page={page}&limit=100"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break
            data = response.json()
            people = data.get('people', [])

            if not people:
                break

            for person in people:
                person_id = person.get("id")
                if last_processed_id and str(person_id) <= str(last_processed_id):
                    continue  # Already processed

                # Fetch full person details
                detail_url = f"https://api.followupboss.com/v1/people/{person_id}?fields=allFields"
                detail_resp = requests.get(detail_url, headers=headers)
                if detail_resp.status_code != 200:
                    continue
                full = detail_resp.json()

                contacts.append({
                    "First Name": full.get("firstName", ""),
                    "Last Name": full.get("lastName", ""),
                    "Email": full.get("emails", [{}])[0].get("value", "") if full.get("emails") else "",
                    "Phone": full.get("phones", [{}])[0].get("value", "") if full.get("phones") else "",
                    "Tags": ", ".join(full.get("tags", [])),
                    "Source": full.get("source", ""),
                    "Created At": full.get("createdAt", ""),
                    "Address": full.get("addresses", [{}])[0].get("formatted", "") if full.get("addresses") else "",
                })
                save_last_id(person_id)
                total_fetched += 1

                if total_fetched >= batch_size:
                    st.success(f"Fetched {batch_size} contacts. You can resume the next batch by running again.")
                    return contacts

            if not data.get("pagination", {}).get("nextPage"):
                break
            page += 1
            progress.progress(min(total_fetched / batch_size, 1.0))

    return contacts

def get_contacts_from_hubspot(api_key):
    client = HubSpot(api_key=api_key)
    all_contacts = []
    after = None
    try:
        while True:
            page = client.crm.contacts.basic_api.get_page(limit=100, after=after) if after else client.crm.contacts.basic_api.get_page(limit=100)
            for c in page.results:
                props = c.properties
                all_contacts.append({
                    "First Name": props.get("firstname", ""),
                    "Last Name": props.get("lastname", ""),
                    "Email": props.get("email", ""),
                    "Phone": props.get("phone", ""),
                    "Created At": props.get("createdate", "")
                })
            after = page.paging.next.after if page.paging and page.paging.next else None
            if not after:
                break
    except ApiException as e:
        st.error(f"HubSpot API error: {e}")
    return all_contacts

def get_contacts_from_salesforce(username, password, security_token):
    sf = Salesforce(username=username, password=password, security_token=security_token)
    query = "SELECT FirstName, LastName, Email, Phone, CreatedDate FROM Contact"
    results = sf.query_all(query)
    return [{
        "First Name": r.get("FirstName", ""),
        "Last Name": r.get("LastName", ""),
        "Email": r.get("Email", ""),
        "Phone": r.get("Phone", ""),
        "Created At": r.get("CreatedDate", "")
    } for r in results['records']]

def export_contacts_to_csv(contacts, filename):
    if not contacts:
        st.warning("No contacts to export.")
        return
    keys = ["First Name", "Last Name", "Email", "Phone", "Tags", "Source", "Created At", "Address"]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(contacts)
    st.success(f"Exported {len(contacts)} contacts to {filename}")
    with open(filename, 'rb') as f:
        st.download_button("Download contacts.csv", f, file_name="contacts.csv")

def main():
    st.title("CRM Contact Exporter")
    crm_choice = st.selectbox("Select CRM", ["Follow Up Boss", "HubSpot", "Salesforce"])

    creds = {}
    if crm_choice == "Follow Up Boss":
        creds["API Key"] = st.text_input("API Key", type="password")
        batch_size = st.number_input("Batch size", min_value=100, max_value=10000, value=1000, step=100)
    elif crm_choice == "HubSpot":
        creds["API Key"] = st.text_input("HubSpot API Key", type="password")
    elif crm_choice == "Salesforce":
        creds["Username"] = st.text_input("Salesforce Username")
        creds["Password"] = st.text_input("Salesforce Password", type="password")
        creds["Security Token"] = st.text_input("Security Token", type="password")

    if st.button("Export Contacts"):
        with st.spinner(f"Exporting contacts from {crm_choice}..."):
            if crm_choice == "Follow Up Boss":
                contacts = get_contacts_from_followupboss(creds["API Key"], batch_size=batch_size)
            elif crm_choice == "HubSpot":
                contacts = get_contacts_from_hubspot(creds["API Key"])
            elif crm_choice == "Salesforce":
                contacts = get_contacts_from_salesforce(creds["Username"], creds["Password"], creds["Security Token"])
            else:
                st.error("Unsupported CRM.")
                return
            export_contacts_to_csv(contacts, "contacts.csv")

if __name__ == "__main__":
    main()
