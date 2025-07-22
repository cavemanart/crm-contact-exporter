import streamlit as st
import requests
import base64

# API key
api_key = st.secrets["fub_api_key"]

# Set base URL and headers
base_url = "https://api.followupboss.com/v1"
headers = {
    "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
    "Content-Type": "application/json"
}

# Fetch Ponds
@st.cache_data(ttl=3600)
def fetch_ponds():
    try:
        response = requests.get(f"{base_url}/ponds", headers=headers)
        response.raise_for_status()
        return response.json().get("ponds", [])
    except Exception as e:
        st.error(f"Failed to fetch ponds: {e}")
        return []

# Fetch contacts from a specific pond
def fetch_contacts_from_pond(pond_id):
    try:
        response = requests.get(f"{base_url}/ponds/{pond_id}/people", headers=headers)
        response.raise_for_status()
        return response.json().get("people", [])
    except Exception as e:
        st.error(f"Failed to fetch contacts from pond: {e}")
        return []

# Load ponds and find Brighton Office
ponds = fetch_ponds()
pond_options = {pond['name']: pond['id'] for pond in ponds}
brighton_pond_id = pond_options.get("Brighton Office")

# UI: Brighton Pond Export
st.subheader("🔹 Brighton Office Pond Contacts")
if brighton_pond_id:
    if st.button("Fetch Contacts from Brighton Office Pond"):
        contacts = fetch_contacts_from_pond(brighton_pond_id)
        if contacts:
            st.success(f"Found {len(contacts)} contacts in Brighton Office pond.")
            for contact in contacts:
                st.json({
                    "Name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}",
                    "Email": contact.get("emails", [{}])[0].get("value", ""),
                    "Phone": contact.get("phones", [{}])[0].get("value", ""),
                    "Stage": contact.get("stage", ""),
                    "Tags": contact.get("tags", []),
                })
        else:
            st.warning("No contacts found in this pond.")
else:
    st.error("Brighton Office pond not found. Make sure the pond exists and is spelled exactly.")

# Optional: Continue with the rest of the app...
