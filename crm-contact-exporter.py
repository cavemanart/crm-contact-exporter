import streamlit as st
import requests
import pandas as pd

# -------------------------------
# Fetch assigned agents
# -------------------------------
def fetch_follow_up_boss_users(api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.followupboss.com/v1/users", headers=headers)

    if response.status_code != 200:
        st.error(f"Error fetching users: {response.status_code} - {response.text}")
        return []

    users = response.json().get("users", [])
    return [{"name": u["name"], "id": u["id"]} for u in users]

# -------------------------------
# Fetch contacts
# -------------------------------
def fetch_follow_up_boss_contacts(api_key, limit=2000, assigned_user_id=None, tag_filter=None):
    contacts = []
    offset = 0
    headers = {"Authorization": f"Bearer {api_key}"}

    while True:
        url = f"https://api.followupboss.com/v1/people?limit=100&offset={offset}"
        if assigned_user_id:
            url += f"&assignedUserId={assigned_user_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        batch = data.get("people", [])
        if not batch:
            break

        for c in batch:
            if tag_filter:
                if any(
                    isinstance(tag, dict) and tag.get("name", "").upper() == tag_filter.upper()
                    for tag in c.get("tags", [])
                ):
                    contacts.append(c)
            else:
                contacts.append(c)

        offset += 100
        if offset >= limit:
            break

    return contacts

# -------------------------------
# Convert contact list to DataFrame
# -------------------------------
def contacts_to_dataframe(contacts):
    rows = []
    for c in contacts:
        row = {
            "Name": c.get("name"),
            "Email": c.get("emails", [{}])[0].get("value", "") if c.get("emails") else "",
            "Phone": c.get("phones", [{}])[0].get("value", "") if c.get("phones") else "",
            "Tags": ", ".join([t["name"] for t in c.get("tags", []) if isinstance(t, dict)]),
            "Stage": c.get("stage"),
            "Assigned To": c.get("assignedTo", {}).get("name", ""),
            "Source": c.get("source", ""),
            "Street": c.get("addresses", [{}])[0].get("street", "") if c.get("addresses") else "",
            "City": c.get("addresses", [{}])[0].get("city", "") if c.get("addresses") else "",
            "State": c.get("addresses", [{}])[0].get("state", "") if c.get("addresses") else "",
            "Zip": c.get("addresses", [{}])[0].get("zip", "") if c.get("addresses") else ""
        }
        rows.append(row)
    return pd.DataFrame(rows)

# -------------------------------
# Streamlit App UI
# -------------------------------
st.title("Follow Up Boss Contact Exporter")

api_key = st.text_input("Enter your Follow Up Boss API Key", type="password")

if api_key:
    users = fetch_follow_up_boss_users(api_key)
    user_options = ["All Agents"] + [user["name"] for user in users]
    selected_user = st.selectbox("Filter by Agent", user_options)
    assigned_user_id = next((user["id"] for user in users if user["name"] == selected_user), None) if selected_user != "All Agents" else None

    tag_filter = st.text_input("Optional: Filter by Tag (case-insensitive, e.g., BRIGHTONPOND)")

    limit = st.slider("How many contacts to fetch?", min_value=100, max_value=5000, value=1000, step=100)

    if st.button("Fetch Contacts"):
        with st.spinner("Fetching contacts..."):
            contacts = fetch_follow_up_boss_contacts(api_key, limit, assigned_user_id, tag_filter)

        if contacts:
            df = contacts_to_dataframe(contacts)
            st.success(f"Fetched {len(df)} contacts.")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "contacts.csv", "text/csv")
        else:
            st.warning("No contacts found with the current filters.")
