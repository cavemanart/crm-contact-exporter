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
            st.error(f"Error fetching contacts: {response.status_code}")
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
    for c in contacts:
        tags = c.get("tags", [])
        for tag in tags:
            try:
                if tag.get("name", "").upper() == tag_filter.upper():
                    filtered.append(c)
                    break
            except AttributeError:
                continue
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
st.title("Follow Up Boss - BrightonPond Tag Exporter")

api_key = st.text_input("Enter your FUB API Key", type="password")

# Agent reference display (not used for filtering)
st.markdown("**Agent (for reference only)**")
st.markdown("- Eric Freeman")

if api_key:
    with st.spinner("Fetching contacts..."):
        contacts = fetch_contacts(api_key)
        pond_contacts = filter_contacts_by_tag(contacts, "BRIGHTONPOND")

    st.success(f"Found {len(pond_contacts)} contacts with tag BRIGHTONPOND")

    if pond_contacts:
        csv_data = export_contacts_to_csv(pond_contacts)
        st.download_button(
            label="📁 Download CSV",
            data=csv_data,
            file_name="brightonpond_contacts.csv",
            mime="text/csv"
        )
        st.write("Sample contacts:")
        for c in pond_contacts[:5]:
            st.write(f"- {c.get('name')} | {c.get('stage')} | {c.get('assignedTo', {}).get('name', '')}")
    else:
        st.warning("No contacts found with tag BRIGHTONPOND.")
