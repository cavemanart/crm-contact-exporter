import streamlit as st
import requests
import csv
import io

# Your Follow Up Boss API key
api_key = st.secrets["FUB_API_KEY"]

# --- Fetch All Contacts with Pagination ---
def fetch_contacts(api_key):
    contacts = []
    limit = 100
    offset = 0
    headers = {
        "Authorization": f"Basic {api_key}"
    }

    while True:
        url = f"https://api.followupboss.com/v1/people?limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code} - {response.text}")
            break
        data = response.json()
        if not data.get("people"):
            break
        contacts.extend(data["people"])
        offset += limit
    return contacts

# --- Manually Filter for Brighton Office Pond ---
def fetch_brighton_pond_contacts(api_key):
    all_contacts = fetch_contacts(api_key)
    brighton_contacts = [
        c for c in all_contacts if c.get("pond", {}).get("name") == "Brighton Office Pond"
    ]
    return brighton_contacts

# --- Fetch All Agents (Reference Only) ---
def fetch_agents(api_key):
    headers = {
        "Authorization": f"Basic {api_key}"
    }
    url = "https://api.followupboss.com/v1/users"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["users"]
    else:
        return []

# --- Streamlit App ---
st.title("📇 FUB Pond Contacts Exporter")

# Fetch agent list (for reference dropdown)
agents = fetch_agents(api_key)
agent_names = [a["name"] for a in agents if a.get("name")]
selected_agent = st.selectbox("Agent (for reference only)", agent_names)

# Fetch contacts from Brighton Office Pond
with st.spinner("Fetching contacts from Brighton Office Pond..."):
    contacts = fetch_brighton_pond_contacts(api_key)

st.success(f"✅ Brighton Office Pond found: Brighton Office Pond")
st.write(f"Contacts found: {len(contacts)}")

# Show contact table
if contacts:
    st.write("### Contact Preview")
    preview_data = [
        {
            "Name": c.get("name"),
            "Email": ", ".join([e["value"] for e in c.get("emails", [])]),
            "Phone": ", ".join([p["value"] for p in c.get("phones", [])]),
            "Stage": c.get("stage"),
            "Assigned To": c.get("assignedTo", {}).get("name"),
            "Pond": c.get("pond", {}).get("name")
        }
        for c in contacts
    ]
    st.dataframe(preview_data)

    # CSV Export
    def convert_to_csv(data):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue().encode("utf-8")

    csv_data = convert_to_csv(preview_data)
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="brighton_pond_contacts.csv",
        mime="text/csv"
    )
else:
    st.warning("No contacts found for Brighton Office Pond.")
