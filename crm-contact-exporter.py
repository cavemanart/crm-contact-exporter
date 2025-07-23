import streamlit as st
import requests
import csv
from io import StringIO

# === CONFIGURATION ===
st.set_page_config(page_title="Follow Up Boss Contact Exporter", layout="wide")

st.title("📤 Follow Up Boss Contact Exporter")
st.markdown("Export your contacts from Follow Up Boss as a CSV file filtered by tag.")

# === INPUT FIELDS ===
api_key = st.text_input("🔑 API Key", type="password")
tag_filter = st.text_input("🏷️ Tag Filter (optional)", value="BRIGHTONPOND")
limit = st.number_input("🔢 Max Contacts to Fetch", min_value=10, max_value=10000, value=500, step=100)

# === CONTACT FETCH FUNCTION ===
def fetch_follow_up_boss_contacts(api_key, limit=None, assigned_user_id=None, tag_filter=None):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    url = "https://api.followupboss.com/v1/people"
    params = {"limit": 100, "offset": 0}
    if assigned_user_id:
        params["assignedUserId"] = assigned_user_id

    all_contacts = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        contacts = data.get("people", [])

        # Filter by tag if specified (assuming tags are list of strings)
        if tag_filter:
            contacts = [c for c in contacts if any((tag or "").upper() == tag_filter.upper() for tag in c.get("tags", []))]

        all_contacts.extend(contacts)

        if limit and len(all_contacts) >= limit:
            break

        if not data.get("people") or len(contacts) < 100:
            break

        params["offset"] += 100

    return all_contacts[:limit] if limit else all_contacts

# === EXPORT FUNCTION ===
def contacts_to_csv(contacts):
    output = StringIO()
    writer = csv.writer(output)
    headers = ["Name", "Email", "Phone", "Tags", "Stage", "Source", "Assigned To", "Street", "City", "State", "Zip"]
    writer.writerow(headers)

    for c in contacts:
        name = c.get("name", "")
        emails = ", ".join([e.get("value", "") for e in c.get("emails", [])])
        phones = ", ".join([p.get("value", "") for p in c.get("phones", [])])
        tags = ", ".join(c.get("tags", []))  # tags are strings
        stage = c.get("stage", "")
        source = c.get("source", "")
        assigned_to = c.get("assignedTo", {}).get("name", "")
        address = c.get("addresses", [{}])[0]
        street = address.get("street", "")
        city = address.get("city", "")
        state = address.get("state", "")
        zip_code = address.get("zipCode", "")

        writer.writerow([name, emails, phones, tags, stage, source, assigned_to, street, city, state, zip_code])

    return output.getvalue()

# === EXPORT BUTTON ===
if st.button("🚀 Export Contacts"):
    if not api_key:
        st.error("Please enter your Follow Up Boss API key.")
    else:
        with st.spinner("Fetching contacts..."):
            try:
                contacts = fetch_follow_up_boss_contacts(api_key, limit=limit, tag_filter=tag_filter)
                if not contacts:
                    st.warning("No contacts found with that tag.")
                else:
                    csv_data = contacts_to_csv(contacts)
                    st.success(f"Exported {len(contacts)} contacts.")

                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name="fub_contacts.csv",
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Error fetching contacts: {e}")
