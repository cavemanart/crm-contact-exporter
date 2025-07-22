import streamlit as st
import requests
import base64

# --- CONFIGURATION ---
FUB_API_KEY = st.secrets.get("FUB_API_KEY", "")  # use secrets in Streamlit cloud or paste here
API_BASE_URL = "https://api.followupboss.com/v1"

headers = {
    "Authorization": f"Basic {base64.b64encode(FUB_API_KEY.encode()).decode()}",
    "Content-Type": "application/json"
}


# --- FETCH PONDS ---
def fetch_ponds():
    try:
        response = requests.get(f"{API_BASE_URL}/ponds", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        st.error(f"Error fetching ponds: {e} - {response.text}")
        return {"ponds": []}


# --- FETCH CONTACTS BY POND ---
def fetch_contacts_by_pond(pond_id):
    try:
        url = f"{API_BASE_URL}/people?pondId={pond_id}&limit=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("people", [])
    except requests.HTTPError as e:
        st.error(f"Error fetching pond contacts: {e} - {response.text}")
        return []


# --- STREAMLIT UI ---
st.title("📇 FUB Contacts by Pond")

if not FUB_API_KEY:
    st.error("API key missing! Please set `FUB_API_KEY` in Streamlit secrets.")
    st.stop()

# --- Get Ponds ---
ponds_data = fetch_ponds()
pond_list = ponds_data.get("ponds", [])
pond_dict = {pond["name"]: pond["id"] for pond in pond_list}

if not pond_dict:
    st.warning("No ponds found.")
    st.stop()

pond_name = st.selectbox("Choose a pond:", list(pond_dict.keys()))
selected_pond_id = pond_dict[pond_name]

# --- Fetch and Display Contacts ---
if st.button("Fetch Contacts from Pond"):
    with st.spinner("Fetching contacts..."):
        contacts = fetch_contacts_by_pond(selected_pond_id)
        st.success(f"Contacts matched: {len(contacts)}")

        if contacts:
            for contact in contacts:
                st.write({
                    "Name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}",
                    "Email": contact.get("emails", [{}])[0].get("value", "N/A"),
                    "Phone": contact.get("phones", [{}])[0].get("value", "N/A"),
                    "Stage": contact.get("stage", "N/A"),
                    "Assigned To": contact.get("assignedTo", {}).get("name", "Unassigned")
                })
        else:
            st.info("No contacts found for this pond.")
