import streamlit as st
import requests
import csv
import io

# --- Streamlit UI ---
st.title("Follow Up Boss Pond Contact Exporter")
api_key = st.text_input("Enter your FUB API Key", type="password")

# Fixed tag used for filtering
tag_name = "BRIGHTONPOND"

# --- Fetch All Agents ---
def fetch_agents(api_key):
    url = "https://api.followupboss.com/v1/users"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get("users", [])

# --- Fetch All Contacts (paginated) ---
def fetch_contacts(api_key):
    all_contacts = []
    limit = 100
    offset = 0
    headers = {"Authorization": f"Bearer {api_key}"}

    while True:
        url = f"https://api.followupboss.com/v1/people?limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        if response.status_code == 400:
            break  # End of pagination
        response.raise_for_status()
        data = response.json()
        contacts = data.get("people", [])
        if not contacts:
            break
        all_contacts.extend(contacts)
        offset += limit

    return all_contacts

# --- Fetch Contacts with Tag ---
def fetch_contacts_with_tag(api_key, tag_name):
    all_contacts = fetch_contacts(api_key)
    matched_contacts = []
    for c in all_contacts:
        tags = c.get("tags", [])
        # If tags are strings
        if any(tag.lower() == tag_name.lower() for tag in tags if isinstance(tag, str)):
            matched_contacts.append(c)
        # If tags are dicts
        elif any(tag.get("name", "").lower() == tag_name.lower() for tag in tags if isinstance(tag, dict)):
            matched_contacts.append(c)
    return matched_contacts

# --- CSV Export ---
def contacts_to_csv(contacts):
    output = io.StringIO()
    writer = csv.writer(output)
    header = ["Name", "Email", "Phone", "Tags", "Stage", "Source", "Assigned To", "Street", "City", "State", "Zip"]
    writer.writerow(header)
    for c in contacts:
        name = c.get("name", "")
        email = c.get("emails", [{}])[0].get("value", "")
        phone = c.get("phones", [{}])[0].get("value", "")
        tags = ", ".join(
            tag.get("name") if isinstance(tag, dict) else tag for tag in c.get("tags", [])
        )
        stage = c.get("stage", "")
        source = c.get("source", "")
        assigned = c.get("assignedTo", {}).get("name", "")
        address = c.get("addresses", [{}])[0]
        street = address.get("street", "")
        city = address.get("city", "")
        state = address.get("state", "")
        zip_code = address.get("zipCode", "")
        row = [name, email, phone, tags, stage, source, assigned, street, city, state, zip_code]
        writer.writerow(row)
    return output.getvalue()

# --- Main Logic ---
if api_key:
    try:
        agents = fetch_agents(api_key)
        agent_names = [a["name"] for a in agents]
        selected_agent = st.selectbox("Agent (for reference only)", ["All"] + agent_names)
        st.write("✅ Brighton Office pond found:", tag_name)

        contacts = fetch_contacts_with_tag(api_key, tag_name)
        st.success(f"Found {len(contacts)} contacts tagged with '{tag_name}'")

        if contacts:
            csv_data = contacts_to_csv(contacts)
            st.download_button(
                label="📥 Download Contacts CSV",
                data=csv_data,
                file_name="brighton_pond_contacts.csv",
                mime="text/csv"
            )
        else:
            st.warning("No contacts found with that tag.")
    except Exception as e:
        st.error(f"Error: {e}")
