import base64
import csv
import streamlit as st
import requests
import time
from io import StringIO

st.set_page_config(page_title="Follow Up Boss Export with Resume Support")

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

def get_followupboss_contact_details(contact_id, headers):
    url = f"https://api.followupboss.com/v1/people/{contact_id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.warning(f"Failed to get details for contact {contact_id}: {response.status_code}")
        return None
    return response.json()

def get_followupboss_people_page(page, limit, headers):
    url = f"https://api.followupboss.com/v1/people?page={page}&limit={limit}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
        return None
    return response.json()

def export_contacts_to_csv(contacts):
    output = StringIO()
    fieldnames = ["First Name", "Last Name", "Email", "Phone", "Tags", "Source", "Created At", "Address"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for c in contacts:
        writer.writerow({
            "First Name": c.get("firstName", ""),
            "Last Name": c.get("lastName", ""),
            "Email": safe_get_first_email(c),
            "Phone": safe_get_first_phone(c),
            "Tags": ", ".join(c.get("tags", [])),
            "Source": c.get("source", ""),
            "Created At": c.get("createdAt", ""),
            "Address": safe_get_first_address(c)
        })

    return output.getvalue()

def main():
    st.title("Follow Up Boss Export with Batch & Resume")

    api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")
    batch_size = st.number_input("Batch size (contacts per run)", min_value=10, max_value=500, value=100, step=10)

    if "contacts" not in st.session_state:
        st.session_state.contacts = []
    if "last_page_fetched" not in st.session_state:
        st.session_state.last_page_fetched = 0

    if st.button("Reset Progress"):
        st.session_state.last_page_fetched = 0
        st.session_state.contacts = []
        st.success("Progress reset! You can start over now.")

    if st.button("Fetch Next Batch"):
        if not api_key:
            st.error("API Key is required")
            return

        token = base64.b64encode(f"{api_key}:".encode()).decode()
        headers = {"Authorization": f"Basic {token}"}

        contacts = []
        fetched_contacts = 0
        page = st.session_state.last_page_fetched + 1

        progress_bar = st.progress(0)
        status_text = st.empty()

        while fetched_contacts < batch_size:
            data = get_followupboss_people_page(page, 100, headers)
            if not data or "people" not in data:
                st.warning("No more contacts or error fetching contacts.")
                break

            people = data["people"]
            if not people:
                st.info("No more contacts found on this page.")
                break

            for basic_contact in people:
                if fetched_contacts >= batch_size:
                    break
                contact_id = basic_contact.get("id")
                if contact_id:
                    full_contact = get_followupboss_contact_details(contact_id, headers)
                    if full_contact:
                        contacts.append(full_contact)
                        fetched_contacts += 1
                        progress = fetched_contacts / batch_size
                        progress_bar.progress(min(progress, 1.0))
                        status_text.text(f"Fetched {fetched_contacts} / {batch_size} contacts...")
                        time.sleep(0.1)  # To avoid API rate limits

            # If batch size not reached, try next page
            page += 1
            if page > 1000:
                st.warning("Reached page limit.")
                break

        st.session_state.contacts = contacts
        st.session_state.last_page_fetched = page - 1

        st.success(f"Fetched {len(contacts)} contacts this batch. Last page fetched: {st.session_state.last_page_fetched}")

    if st.session_state.contacts:
        csv_data = export_contacts_to_csv(st.session_state.contacts)
        st.download_button("Download CSV of this batch", data=csv_data, file_name=f"followupboss_contacts_page_{st.session_state.last_page_fetched}.csv", mime="text/csv")

if __name__ == "__main__":
    main()
