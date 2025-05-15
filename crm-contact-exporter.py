import os
import csv
import json
import base64
import streamlit as st
import requests

PROGRESS_FILE = "progress.json"
CSV_FILE = "contacts_export.csv"

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

    headers = ["First Name", "Last Name", "Email", "Phone", "Address", "Tags", "Source", "Created At"]

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

def get_followupboss_contacts(api_key, start_page=1):
    contacts = []
    page = start_page
    batch_size = 100
    has_next = True
    total_fetched = 0

    auth_string = f"{api_key}:".encode("utf-8")
    headers = {
        "Authorization": f"Basic {base64.b64encode(auth_string).decode('utf-8')}"
    }

    with st.spinner("Fetching contacts..."):
        progress = st.progress(0)
        while has_next:
            url = f"https://api.followupboss.com/v1/people?page={page}&limit={batch_size}"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                return

            data = response.json()
            batch = data.get("people", [])
            if not batch:
                break

            export_contacts_to_csv(batch)
            total_fetched += len(batch)
            progress.progress(min(1.0, total_fetched / 13000))

            page += 1
            save_progress({"page": page})
            has_next = data.get("pagination", {}).get("nextPage", False)

def main():
    st.title("CRM Contact Exporter")

    crm_choice = st.selectbox("Select CRM", ["Follow Up Boss"])  # Add HubSpot and Salesforce later

    api_key = st.text_input("API Key", type="password")
    progress_state = load_progress()
    resume = False
    if progress_state.get("page"):
        resume = st.checkbox(f"Resume from page {progress_state['page']}?", value=True)

    reset = st.checkbox("Start fresh?")
    if st.button("Start Export"):
        if reset:
            reset_progress()

        if api_key:
            start_page = progress_state.get("page", 1) if resume else 1
            get_followupboss_contacts(api_key, start_page=start_page)
            st.success("Contacts export complete.")

            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "rb") as f:
                    st.download_button("Download CSV", f, file_name="contacts_export.csv", mime="text/csv")
            else:
                st.error("No CSV file found. Export may have failed.")
        else:
            st.error("Please enter your API key.")

if __name__ == "__main__":
    main()
