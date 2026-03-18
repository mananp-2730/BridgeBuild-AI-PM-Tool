import streamlit as st
import pandas as pd
import re

def extract_average_cost(raw_cost_str):
    """Helper function to turn '15000-20000' into a mathematical average for the pipeline."""
    if not raw_cost_str or raw_cost_str == "0-0" or raw_cost_str == "N/A (Design Phase)" or raw_cost_str == "N/A (Engineering Phase)":
        return 0
    
    # Extract all numbers from the string
    numbers = re.findall(r'\d+', str(raw_cost_str).replace(',', ''))
    if not numbers:
        return 0
    if len(numbers) == 1:
        return int(numbers[0])
    if len(numbers) >= 2:
        return (int(numbers[0]) + int(numbers[1])) / 2
    return 0

def render_admin_dashboard(supabase):
    st.title("Admin Control Center")
    st.markdown("### BridgeBuild AI Global Oversight & Access Control")
    
    # Create a clean tabbed layout so the Admin Hub doesn't get cluttered
    tab1, tab2 = st.tabs(["Global Analytics", "Team Role Management"])

    # ==========================================
    # TAB 1: THE "GOD VIEW" ANALYTICS
    # ==========================================
    with tab1:
        try:
            # Fetch EVERY ticket in the entire company
            all_tickets_response = supabase.table("tickets").select("*").execute()
            all_tickets = all_tickets_response.data
            
            if not all_tickets:
                st.info("No projects generated in the company yet.")
            else:
                total_projects = len(all_tickets)
                total_pipeline_value = sum([extract_average_cost(t.get('raw_cost', '0-0')) for t in all_tickets])
                
                # Count bottlenecks by targeting department
                pm_queue = len([t for t in all_tickets if t.get('target_department') == 'PM'])
                design_queue = len([t for t in all_tickets if t.get('target_department') == 'Design'])
                eng_queue = len([t for t in all_tickets if t.get('target_department') == 'Engineering'])
                completed = len([t for t in all_tickets if t.get('status') == 'Ready for Dev'])

                st.markdown("#### Organization Pipeline Overview")
                
                # Top Row Metrics (Executive Containers)
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    with st.container(border=True):
                        st.metric("Total AI Generations 🤖", total_projects)
                with col_m2:
                    with st.container(border=True):
                        st.metric("Total Pipeline Value 💰", f"${total_pipeline_value:,.2f}")
                with col_m3:
                    with st.container(border=True):
                        st.metric("Fully Scoped & Ready ✅", completed)

                st.write("")
                st.markdown("#### Live Department Bottlenecks")
                
                # Second Row Metrics (Queue Warnings)
                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    with st.container(border=True):
                        st.markdown("**📝 Awaiting PM Scoping**")
                        if pm_queue > 0: st.error(f"## {pm_queue} Ticket(s)")
                        else: st.success("## 0 Tickets")
                with col_b2:
                    with st.container(border=True):
                        st.markdown("**🎨 Awaiting UI/UX Design**")
                        if design_queue > 0: st.error(f"## {design_queue} Ticket(s)")
                        else: st.success("## 0 Tickets")
                with col_b3:
                    with st.container(border=True):
                        st.markdown("**⚙️ Awaiting Engineering**")
                        if eng_queue > 0: st.error(f"## {eng_queue} Ticket(s)")
                        else: st.success("## 0 Tickets")

                st.divider()
                st.markdown("#### Live Project Radar")
                
                # Clean up the data for a beautiful Admin Table
                radar_data = []
                for t in all_tickets:
                    radar_data.append({
                        "Creation Date": t.get("created_at", "").split("T")[0],
                        "Project Summary": t.get("summary", "Unknown")[:80] + "...",
                        "Current Status": t.get("status", "Unknown"),
                        "Target Dept": t.get("target_department", "None"),
                        "Est. Time": t.get("time", "Unknown"),
                    })
                
                radar_df = pd.DataFrame(radar_data)
                
                # Sort by newest first
                radar_df = radar_df.sort_values(by="Creation Date", ascending=False)
                
                # Display interactive, read-only dataframe
                st.dataframe(
                    radar_df, 
                    use_container_width=True, 
                    hide_index=True,
                    height=400,
                    column_config={
                        "Creation Date": st.column_config.TextColumn("Date", width="small"),
                        "Project Summary": st.column_config.TextColumn("Project Vision", width="large"),
                        "Current Status": st.column_config.TextColumn("Status", help="Current stage in the pipeline", width="medium"),
                        "Target Dept": st.column_config.TextColumn("Owner", width="small"),
                        "Est. Time": st.column_config.TextColumn("Timeline", width="small")
                    }
                )

        except Exception as e:
            st.error(f"Error loading Global Analytics: {str(e)}")

    # ==========================================
    # TAB 2: TEAM MANAGEMENT 
    # ==========================================
    with tab2:
        st.write("")
        st.markdown("#### Active Directory")
        st.info("Assign department dashboards to users by clicking their 'Role' cell below, selecting a new department, and hitting Save.")

        try:
            response = supabase.table("profiles").select("*").execute()
            profiles_data = response.data
            
            if not profiles_data:
                st.warning("No user profiles found.")
            else:
                df = pd.DataFrame(profiles_data)
                roles_list = ["pm", "sales", "engineering", "design", "freelancer", "admin"]
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "id": st.column_config.TextColumn("User ID", disabled=True, width="medium"),
                        "role": st.column_config.SelectboxColumn(
                            "Department Role",
                            help="Assign the user's dashboard access level.",
                            options=roles_list,
                            required=True,
                            width="medium"
                        ),
                        "currency": st.column_config.TextColumn("Currency", disabled=True, width="small"),
                        "rate_standard": st.column_config.TextColumn("Rate Standard", disabled=True, width="medium"),
                        "ai_model": st.column_config.TextColumn("AI Model", disabled=True, width="medium"),
                        "dark_mode": st.column_config.CheckboxColumn("Dark Mode", disabled=True, width="small")
                    },
                    hide_index=True,
                    key="admin_role_editor",
                    use_container_width=True,
                    height=400
                )

                st.write("")
                
                if st.button("Save Changes to Database", type="primary"):
                    with st.spinner("Pushing updates to enterprise servers..."):
                        updates_made = False
                        
                        for index, row in edited_df.iterrows():
                            original_role = df.loc[index, 'role']
                            new_role = row['role']
                            
                            if original_role != new_role:
                                supabase.table("profiles").update({"role": new_role}).eq("id", row['id']).execute()
                                updates_made = True
                        
                        if updates_made:
                            st.success("User roles updated successfully!")
                            st.rerun() 
                        else:
                            st.info("No changes detected.")
                            
        except Exception as e:
            st.error(f"Error loading Admin Directory: {str(e)}")
