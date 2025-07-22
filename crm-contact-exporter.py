import streamlit as st
import requests
import base64
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="Brighton Office Pond Export", layout="wide")
st.title("🏡 Follow Up Boss: Brighton Office Pond Contacts Export")

# --- API Setup ---
api_key = st.secrets["fub_api_key"]  # Replace with your key if not using secrets
base_url = "https://api.followupboss.com/v1"
headers = {
    "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
    "Content-Type": "application/json"
}

# --- Fetch All Ponds ---
@st.cache_data(ttl=3600)
def fetch_ponds():
    try:
        response = requests.get(f"{base_url}/ponds", headers=headers)
        response.raise_for_status()
        return response.json().get("ponds", [])
    except Exception as e:
        st.error(f"Failed to fetch ponds: {e}")
        return []

# --- Fetch Contacts in Specific Pond ---
def fetch_contacts_from_pond(pond_id):
    all_contacts = []
    limit = 100
    offset = 0

    while True:
        try:
            url = f"{base_url}/ponds/{pond_id}/people?limit={limit}&offset={offset}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            people = response.json().get("people", [])
            all_contacts.extend(people)

            if len(people) < limit:
                break
            offset += limit
        except Exception as e:
            st.error(f"Failed to fetch contacts from pond: {e}")
            break

    return all_contacts

# --- Get Brighton Pond ID ---
ponds = fetch_ponds()
pond_options = {pond['name']: pond['id'] for pond in ponds}
brighton_pond_id = pond_options.get("Brighton Office")

# --- UI ---
if not brighton_pond_id:
    st.error("❌ Could not find 'Brighton Office' pond. Double-check the name in Follow Up Boss.")
else:
    if st.button("📥 Fetch Contacts from Brighton Office Pond"):
        with st.spinner("Fetching contacts..."):
            contacts = fetch_contacts_from_pond(brighton_pond_id)

        if not contacts:
            st.warning("No contacts found in Brighton Office pond.")
        else:
            st.success(f"✅ Found {len(contacts)} contacts.")

            # Format contacts
            rows = []
            for contact in contacts:
                rows.append({
                    "Name": f"{contact.get('firstName', '')} {contact.get('lastName', '')}",
                    "Email": contact.get("emails", [{}])[0].get("value", ""),
                    "Phone": contact.get("phones", [{}])[0].get("value", ""),
                    "Stage": contact.get("stage", ""),
                    "Tags": ", ".join(contact.get("tags", [])),
                    "Source": contact.get("source", ""),
                    "Created": contact.get("created", "")[:10]
                })

            df = pd.DataFrame(rows)

            st.dataframe(df, use_container_width=True)

            # Export option
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="brighton_office_contacts.csv",
                mime="text/csv"
            )
