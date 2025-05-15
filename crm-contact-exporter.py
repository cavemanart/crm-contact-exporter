import streamlit as st
import requests
import csv
import base64
import time
import hashlib
import hmac
import uuid

CSV_FILE = "contacts.csv"

def fetch_follow_up_boss_contacts(api_key, limit):
    headers = {
        "Authorization": "Basic " + base64.b64encode((api_key + ":").encode()).decode()
    }
    url = "https://api.followupboss.com/v1/people"
    contacts = []
    offset = 0
    with st.spinner("Fetching contacts from Follow Up Boss..."):
        while len(contacts) < limit:
            params = {"limit": 100, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Follow Up Boss API error: {response.status_code} {response.text}")
                break
            batch = response.json().get("people", [])
            if not batch:
                break
            contacts.extend(batch)
            offset += 100
            st.progress(min(len(contacts) / limit, 1.0))
            time.sleep(0.2)
    return contacts[:limit]

def fetch_kvcore_contacts(api_key, limit):
    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://api.kvcore.com/v2/public/contacts"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"kvCORE API error: {response.status_code} {response.text}")
        return []
    return response.json().get("data", [])[:limit]

def fetch_boomtown_contacts(api_key, api_secret, limit):
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    path = "/contacts"
    string_to_sign = f"{path}{timestamp}{nonce}"
    signature = hmac.new(api_secret.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()
    headers = {
        "X-Boomtown-Token": api_key,
        "X-Boomtown-Signature": signature,
        "X-Boomtown-Timestamp": timestamp,
        "X-Boomtown-Nonce": nonce,
    }
    url = f"https://api.goboomtown.com/v3{path}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"BoomTown API error: {response.status_code} {response.text}")
        return []
    return response.json().get("contacts", [])[:limit]

def fetch_liondesk_contacts(access_token, limit):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.liondesk.com/v1/contacts"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"LionDesk API error: {response.status_code} {response.text}")
        return []
    return response.json().get("contacts", [])[:limit]

def export_contacts_to_csv(contacts, crm_type):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "First Name", "Last Name", "Email", "Phone", "Tags", "Source", "Created At", "Street", "City", "State", "Zip"
        ])
        writer.writeheader()
        for c in contacts:
            if crm_type == "Follow Up Boss":
                writer.writerow({
                    "First Name": c.get("firstName", ""),
                    "Last Name": c.get("lastName", ""),
                    "Email": c.get("emails")[0]["value"] if c.get("emails") else "",
                    "Phone": c.get("phones")[0]["value"] if c.get("phones") else "",
                    "Tags": ", ".join(c.get("tags", [])),
                    "Source": c.get("source", ""),
                    "Created At": c.get("created", ""),
                    "Street": c.get("addresses")[0]["street"] if c.get("addresses") else "",
                    "City": c.get("addresses")[0]["city"] if c.get("addresses") else "",
                    "State": c.get("addresses")[0]["state"] if c.get("addresses") else "",
                    "Zip": c.get("addresses")[0]["code"] if c.get("addresses") else "",
                })
            else:
                writer.writerow({
                    "First Name": c.get("first_name", ""),
                    "Last Name": c.get("last_name", ""),
                    "Email": c.get("email", ""),
                    "Phone": c.get("phone", ""),
                    "Tags": "",
                    "Source": c.get("source", ""),
                    "Created At": c.get("created", ""),
                    "Street": c.get("street", ""),
                    "City": c.get("city", ""),
                    "State": c.get("state", ""),
                    "Zip": c.get("zip", ""),
                })

def main():
    st.set_page_config(page_title="CRM Contact Exporter", layout="centered")
    st.markdown(
        """
        <style>
        div[data-baseweb="select"] > div { background-color: white !important; color: black !important; }
        div[data-baseweb="select"] > div:hover { background-color: black !important; color: white !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("CRM Contact Exporter")
    st.write("This tool pulls your CRM contacts and exports them to a CSV.")

    crm_type = st.selectbox("Select CRM", ["Follow Up Boss", "kvCORE", "BoomTown", "LionDesk"])

    limit = st.number_input("Number of contacts to export", min_value=1, max_value=10000, value=100)

    api_key = st.text_input(f"Enter your {crm_type} API Key", type="password")

    secret = ""
    if crm_type == "BoomTown":
        secret = st.text_input("Enter your BoomTown API Secret", type="password")

    if st.button("Export Contacts"):
        if not api_key:
            st.error("Please enter your API Key.")
            return

        contacts = []
        if crm_type == "Follow Up Boss":
            contacts = fetch_follow_up_boss_contacts(api_key, limit)
        elif crm_type == "kvCORE":
            contacts = fetch_kvcore_contacts(api_key, limit)
        elif crm_type == "BoomTown":
            if not secret:
                st.error("Please enter your BoomTown secret.")
                return
            contacts = fetch_boomtown_contacts(api_key, secret, limit)
        elif crm_type == "LionDesk":
            contacts = fetch_liondesk_contacts(api_key, limit)

        if contacts:
            export_contacts_to_csv(contacts, crm_type)
            with open(CSV_FILE, "rb") as f:
                st.success(f"Exported {len(contacts)} contacts to {CSV_FILE}")
                st.download_button("Download CSV", f, file_name=CSV_FILE, mime="text/csv")

if __name__ == "__main__":
    main()
