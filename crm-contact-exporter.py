import streamlit as st
import requests
import csv
import io

# --- FUB API Helper ---
def fetch_contacts(api_key, limit=5000):
    url = "https://api.followupboss.com/v1/people"
    headers = {"Authorization": f"Bearer {api_key}"}
    contacts = []
    offset = 0

    while True:
        params = {"limit": 100, "offset": offset}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            st.error(f"Error fetching contacts: {response.status_code} - {response.text}")
            break
        data = response.json()
        batch = data.get("people", [])
        contacts.extend(batch)
        if len(batch) < 100 or len(contacts) >= limit:
            break
        offset += 100
    return contacts

# --- Filter Contacts by Tag ---
def filter_contacts_by_tag(contacts, tag_filter):
    filtered = []
    for contact in contacts:
        tags = contact.get("tags", [])
        for tag in tags:
            if isinstance(tag, dict) and tag.get("name", "").upper() == tag_filter.upper():
                filtered.append(contact)
                break
    return filtered

# --- Export to CSV ---
def export_contacts_to_csv(contacts):
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["Name", "Email", "Phone", "Stage", "Tags", "Assigned To"]
    writer.writerow(headers)
    for c in contacts:
        name = c.get("name", "")
        email = c.get("emails", [{}])[0].get("value", "")
        phone = c.get("phones", [{}])[0].get("value", "")
        stage = c.get("stage", "")
        tags = ", ".join([t.get("name", "") for t in c.get("tags", [])])
        assigned_to = c.get("assignedTo", {}).get("name", "")
        writer.writerow([name, email, phone, stage, tags, assigned_to])
    return output.getvalue()

# --- Streamlit UI ---
st.title("📤 FUB Contact Exporter — Filter by Tag")

# API Key input
api_key = st.text_input("🔑 Enter your Follow Up Boss API Key", type="password")

# Tag filter input
tag_filter = st.text_input("🏷️ Tag to filter by (case-insensitive)", value="BRIGHTONPOND")

# Agent reference display (optional, static info)
st.markdown("**Example Agent (for reference only)**")
st.markdown("- Eric Freeman")

if api_key and tag_filter:
    with st.spinner("Fetching and filtering contacts..."):
        all_contacts = fetch_contacts(api_key)
        tagged_contacts = filter_contacts_by_tag(all_contacts, tag_filter)

    st.success(f"✅ Found {len(tagged_contacts)} contacts with tag '{tag_filter}'")

    if tagged_contacts:
        csv_data = export_contacts_to_csv(tagged_contacts)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"{tag_filter.lower()}_contacts.csv",
            mime="text/csv"
        )

        st.subheader("🔍 Sample Contacts Preview")
        for c in tagged_contacts[:5]:
            st.write(f"- **{c.get('name')}** | {c.get('stage')} | Assigned to: {c.get('assignedTo', {}).get('name', '')}")
    else:
        st.warning(f"No contacts found with tag '{tag_filter}'.")
