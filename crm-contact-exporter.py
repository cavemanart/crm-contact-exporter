import streamlit as st
import requests
import pandas as pd
import base64

# --- Auth Headers ---
def get_headers(api_key):
    return {
        "Authorization": f"Basic {base64.b64encode(api_key.encode()).decode()}",
        "Content-Type": "application/json"
    }

# --- Fetch All Agents ---
def fetch_agents(api_key):
    url = "https://api.followupboss.com/v1/users"
    headers = get_headers(api_key)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["users"]

# --- Fetch All Ponds ---
def fetch_ponds(api_key):
    url = "https://api.followupboss.com/v1/ponds"
    headers = get_headers(api_key)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["ponds"]

# --- Fetch All Contacts ---
def fetch_contacts(api_key):
    url = "https://api.followupboss.com/v1/people"
    headers = get_headers(api_key)
    contacts = []
    limit = 100
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        batch = response.json()["people"]
        if not batch:
            break
        contacts.extend(batch)
        offset += limit
    return contacts

# --- Filter Contacts by Pond ---
def fetch_contacts_from_pond(api_key, pond_id):
    all_contacts = fetch_contacts(api_key)
    pond_contacts = [c for c in all_contacts if c.get("pond", {}).get("id") == pond_id]
    return pond_contacts

# --- CSV Export ---
def convert_contacts_to_csv(contacts):
    rows = []
    for c in contacts:
        row = {
            "Name": f"{c.get('firstName', '')} {c.get('lastName', '')}",
            "Email": c.get("primaryEmail", ""),
            "Phone": c.get("primaryPhone", ""),
            "Stage": c.get("stage", ""),
            "Source": c.get("source", ""),
            "Assigned Agent": c.get("assignedTo", {}).get("name", ""),
            "Tags": ", ".join(c.get("tags", []))
        }
        address = c.get("addresses", [{}])[0]
        row.update({
            "Street": address.get("street", ""),
            "City": address.get("city", ""),
            "State": address.get("state", ""),
            "Zip": address.get("zipCode", "")
        })
        rows.append(row)
    return pd.DataFrame(rows)

# --- Streamlit App ---
st.title("📇 FUB Contacts from Brighton Office Pond")

api_key = st.text_input("Enter Follow Up Boss API Key", type="password")

if api_key:
    try:
        # Fetch agents and ponds
        agents = fetch_agents(api_key)
        ponds = fetch_ponds(api_key)

        agent_names = [a["name"] for a in agents]
        selected_agent = st.selectbox("Agent (for reference only)", agent_names)

        # Locate Brighton Office pond
        brighton_pond = next((p for p in ponds if "brighton office" in p["name"].lower()), None)

        if not brighton_pond:
            st.error("❌ Brighton Office pond not found.")
        else:
            st.success(f"✅ Brighton Office pond found: {brighton_pond['name']}")
            pond_contacts = fetch_contacts_from_pond(api_key, brighton_pond["id"])
            st.write(f"📦 Contacts in Brighton Office Pond: {len(pond_contacts)}")

            if pond_contacts:
                df = convert_contacts_to_csv(pond_contacts)
                st.dataframe(df)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "brighton_pond_contacts.csv", "text/csv")
            else:
                st.warning("No contacts found in the Brighton Office pond.")

    except requests.HTTPError as e:
        st.error(f"HTTP Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
