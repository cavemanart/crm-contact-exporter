import requests
import streamlit as st
import csv
import io
import base64

# --- CONFIGURATION ---
API_KEY = "your_api_key_here"
HEADERS = {
    "Authorization": f"Basic {base64.b64encode((API_KEY + ':').encode()).decode()}",
    "Content-Type": "application/json"
}

# --- Fetch Agents ---
def fetch_agents():
    response = requests.get("https://api.followupboss.com/v1/users", headers=HEADERS)
    response.raise_for_status()
    return response.json().get("users", [])

# --- Fetch Ponds ---
def fetch_ponds():
    response = requests.get("https://api.followupboss.com/v1/ponds", headers=HEADERS)
    response.raise_for_status()
    return response.json().get("ponds", [])

# --- Fetch ALL Contacts (paginated) ---
def fetch_contacts():
    contacts = []
    offset = 0
    limit = 100
    while True:
        url = f"https://api.followupboss.com/v1/people?limit={limit}&offset={offset}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 400:
            break
        response.raise_for_status()
        page = response.json().get("people", [])
        if not page:
            break
        contacts.extend(page)
        offset += limit
    return contacts

# --- Filter Contacts by Pond ---
def fetch_contacts_from_pond(pond_id):
    all_contacts = fetch_contacts()
    filtered = []
    for contact in all_contacts:
        if contact.get("pond", {}).get("id") == pond_id:
            filtered.append(contact)
    return filtered

# --- Convert to CSV ---
def convert_to_csv(contacts):
    if not contacts:
        return None
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "name", "email", "phone", "stage"])
    writer.writeheader()
    for contact in contacts:
        writer.writerow({
            "id": contact.get("id"),
            "name": contact.get("name"),
            "email": contact.get("emails")[0]["value"] if contact.get("emails") else "",
            "phone": contact.get("phones")[0]["value"] if contact.get("phones") else "",
            "stage": contact.get("stage", "")
        })
    return output.getvalue()

# --- UI ---
st.title("📇 FUB Pond Contacts Export")

# Fetch and list agents (optional display)
try:
    agents = fetch_agents()
    st.markdown("### Agent (for reference only)")
    for agent in agents:
        st.write(agent.get("name"))
except Exception as e:
    st.error(f"Error fetching agents: {e}")

# Get Brighton Office Pond ID
try:
    ponds = fetch_ponds()
    brighton_pond = next((p for p in ponds if "brighton" in p["name"].lower()), None)
    if brighton_pond:
        st.success(f"✅ Brighton Office pond found: {brighton_pond['name']}")
        contacts = fetch_contacts_from_pond(brighton_pond["id"])
        st.markdown(f"### ✅ {len(contacts)} contacts found in Brighton Office Pond")
        
        if contacts:
            csv_data = convert_to_csv(contacts)
            b64 = base64.b64encode(csv_data.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="brighton_pond_contacts.csv">📥 Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.warning("No contacts found in Brighton Office Pond.")
    else:
        st.error("❌ Brighton Office Pond not found.")
except Exception as e:
    st.error(f"Error: {e}")
