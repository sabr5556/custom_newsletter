import streamlit as st
import pandas as pd
import user_manager
import generator # The new script above

st.set_page_config(page_title="The Daily Distill", layout="wide")

# Sidebar
st.sidebar.title("Admin Panel")
conn = user_manager.get_db_connection()
try:
    # Load users to populate dropdown
    users = pd.read_sql("SELECT * FROM users", conn)
    user_list = users['email'].tolist()
except:
    user_list = []
conn.close()

choice = st.sidebar.selectbox("Select User", ["Create New User"] + user_list)

# --- CREATE USER ---
if choice == "Create New User":
    st.title("New Subscriber")
    with st.form("new_user"):
        first = st.text_input("First Name")
        last = st.text_input("Last Name")
        email = st.text_input("Email")
        prefs = st.text_area("Preferences (Topics, People, Companies)")
        
        if st.form_submit_button("Save Profile"):
            user_manager.add_user(email, first, last, prefs)
            st.success("User added! Refresh to see them in the list.")

# --- VIEW / GENERATE ---
else:
    # Get user data
    conn = user_manager.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (choice,)).fetchone()
    conn.close()
    
    st.title(f"Newsletter for {user['first_name']} {user['last_name']}")
    
    tab1, tab2 = st.tabs(["Profile", "Newsletter"])
    
    with tab1:
        # Edit Profile
        new_prefs = st.text_area("Update Preferences", value=user['preferences'], height=150)
        if st.button("Update Preferences"):
            user_manager.add_user(user['email'], user['first_name'], user['last_name'], new_prefs)
            st.toast("Updated!")
            
    with tab2:
        # The "Go" Button
        if st.button("🚀 Generate Newsletter (Run Pipeline)"):
            with st.spinner("Filtering > Researching > Writing..."):
                generator.generate_for_user(user['user_id'])
                st.success("Newsletter Generated!")
                st.rerun()
        
        st.divider()
        
        # Display the stored newsletter
        if user['newsletter_content']:
            st.markdown(user['newsletter_content'])
        else:
            st.info("No newsletter generated yet.")