import os
import csv
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

PROGRESS_FILE = "progress.txt"
CSV_FILE = "contacts.csv"

def load_last_page():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return int(f.read().strip())
    return 1

def save_last_page(page):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(page))

def reset_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

def fetch_contacts(api_key, page, limit):
    url = f"https://api.followupboss.com/v1/people?page={page}&limit={limit}"
    response = requests.get(url, auth=HTTPBasicAuth(api_key, ""), headers={"Accept": "application/json"})
    if response.status_code != 200:
        st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
        return []
    data = response.json()
    return data.get("people", [])

def format_contact(contact):
    address = contact.get("primaryAddress") or {}
    return {
        "First Name": contact.get("firstName", ""),
        "Last Name": contact.get("lastName", ""),
        "Email": contact.get("emails", [{}])[0].get("value", "") if contact.get("emails") else "",
        "Phone": contact.get("phones", [{}])[0].get("value", "") if contact.get("phones") else "",
        "Tags": ", ".join(contact.get("tags", [])),
        "Source": contact.get("source", ""),
        "Created At": contact.get("createdAt", ""),
        "Street": address.get("street", ""),
        "City": address.get("city", ""),
        "State": address.get("state", ""),
        "Zip": address.get("zip", "")
    }

def export_to_csv(contacts, filename):
    if not contacts:
        return
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=contacts[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(contacts)

def main():
    st.title("Follow Up Boss Contact Exporter")

    st.markdown("This tool pulls your Follow Up Boss contacts and exports them to a CSV.")
    api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

    reset = st.checkbox("Start over (clear progress and CSV)")
    if reset:
        reset_progress()
        st.success("Progress and previous CSV removed.")

    contact_limit = st.number_input("Number of contacts to export this session", min_value=100, max_value=10000, value=500, step=100)

    if st.button("Start Export"):
        if not api_key:
            st.error("API key is required.")
            return

        page = load_last_page()
        batch_size = 100
        total_fetched = 0

        progress_bar = st.progress(0)
        contacts_exported = 0

        while total_fetched < contact_limit:
            contacts = fetch_contacts(api_key, page, batch_size)
            if not contacts:
                st.info("No more contacts to fetch.")
                break

            formatted_contacts = [format_contact(c) for c in contacts]
            export_to_csv(formatted_contacts, CSV_FILE)

            total_fetched += len(contacts)
            page += 1
            save_last_page(page)

            contacts_exported += len(contacts)
            progress = min(contacts_exported / contact_limit, 1.0)
            progress_bar.progress(progress)

            if len(contacts) < batch_size:
                break

        if contacts_exported > 0:
            st.success(f"Exported {contacts_exported} contacts to {CSV_FILE}.")
            with open(CSV_FILE, "rb") as f:
                st.download_button("Download CSV", data=f, file_name=CSV_FILE, mime="text/csv")
        else:
            st.warning("No contacts exported.")

if __name__ == "__main__":
    main()
