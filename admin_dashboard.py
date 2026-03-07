import streamlit as st
import pandas as pd

def render_admin_dashboard(supabase):
    
    st.title("Team Role Management")
    st.markdown("### BridgeBuild AI Access Control")
    st.info("Assign department dashboards to users by clicking their 'Role' cell below, selecting a new department, and hitting Save.")

    try:
        # 1. Fetch all profiles from Supabase
        response = supabase.table("profiles").select("*").execute()
        profiles_data = response.data
        
        if not profiles_data:
            st.warning("No user profiles found.")
            return

        # 2. Convert to a Pandas DataFrame for the interactive editor
        df = pd.DataFrame(profiles_data)
        
        # 3. Setup the allowed roles for the dropdown
        roles_list = ["pm", "sales", "engineering", "design", "freelancer", "admin"]
        
        st.markdown("#### Active Directory")
        
        # 4. Render the interactive Data Editor
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.TextColumn("User ID", disabled=True),
                "role": st.column_config.SelectboxColumn(
                    "Department Role",
                    help="Assign the user's dashboard access level.",
                    options=roles_list,
                    required=True
                ),
                # Lock the user's personal preferences so the admin can't accidentally change them
                "currency": st.column_config.TextColumn("Currency", disabled=True),
                "rate_standard": st.column_config.TextColumn("Rate Standard", disabled=True),
                "ai_model": st.column_config.TextColumn("AI Model", disabled=True)
            },
            hide_index=True,
            key="admin_role_editor",
            use_container_width=True
        )

        st.write("")
        
        # 5. The Save Logic
        if st.button("Save Changes to Database", type="primary"):
            with st.spinner("Pushing updates to enterprise servers..."):
                updates_made = False
                
                # Compare the edited dataframe to the original to find what changed
                for index, row in edited_df.iterrows():
                    original_role = df.loc[index, 'role']
                    new_role = row['role']
                    
                    if original_role != new_role:
                        # Push just the updated role to Supabase
                        supabase.table("profiles").update({"role": new_role}).eq("id", row['id']).execute()
                        updates_made = True
                
                if updates_made:
                    st.success("User roles updated successfully!")
                    st.rerun() # Refresh the app to lock in the changes
                else:
                    st.info("No changes detected.")
                    
    except Exception as e:
        st.error(f"Error loading Admin Directory: {str(e)}")
