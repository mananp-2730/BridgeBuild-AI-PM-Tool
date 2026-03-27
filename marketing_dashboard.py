import streamlit as st
import json
from google import genai
from google.genai import types
from prompts import get_marketing_prompt
from utils import clean_json_output, safe_parse_json

def render_marketing_dashboard(supabase):
    st.title("BridgeBuild AI - Marketing Studio ")
    st.markdown("### Translate technical features into high-converting Go-To-Market copy.")

    api_key = st.secrets.get("GOOGLE_API_KEY")
    user_prefs = st.session_state.get("user_prefs", {})
    model_choice = user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")

    # --- 1. PROJECT SELECTOR ---
    st.markdown("#### Select Project for GTM Launch")
    try:
        # Fetch projects that have moved past the initial Draft phase
        db_response = supabase.table("tickets").select("*").neq("status", "Draft").order("created_at", desc=True).execute()
        active_projects = db_response.data
        
        if not active_projects:
            st.info("No approved projects available for marketing yet. Process a ticket in the Sales or PM hub first!")
            return
            
        project_options = {f"{p['summary'][:60]}... (Status: {p['status']})": p for p in active_projects}
        selected_project_name = st.selectbox("Select an internal project:", list(project_options.keys()))
        selected_project = project_options[selected_project_name]
        
    except Exception as e:
        st.error(f"Failed to load projects: {str(e)}")
        return

    st.divider()

    # --- 2. GENERATION ENGINE ---
    if st.button("Generate Marketing Copy", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                MARKETING_PROMPT = get_marketing_prompt()

                with st.status("Analyzing technical specs & generating copy...", expanded=True) as status:
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    
                    # Feed the entire historical JSON of the project to the Marketing AI
                    project_context = f"PROJECT DATA:\n{selected_project.get('full_data', selected_project.get('summary'))}"
                    
                    st.write("Drafting Landing Page & SEO...")
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=MARKETING_PROMPT, 
                            temperature=0.7, # Slightly higher temperature for creative copywriting
                            response_mime_type="application/json"
                        ),
                        contents=[project_context]
                    )
                    
                    st.write("Formatting Marketing Assets...")
                    data, error_msg = safe_parse_json(response.text)
                    
                    if error_msg:
                        status.update(label="Generation Failed", state="error", expanded=True)
                        st.error(error_msg)
                        st.stop()
                    else:
                        status.update(label="Marketing Assets Ready!", state="complete", expanded=False)
                        st.session_state.active_marketing_data = data

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # --- 3. RENDER OUTPUT UI ---
    if st.session_state.get("active_marketing_data"):
        data = st.session_state.active_marketing_data
        
        st.write("")
        st.success("Go-To-Market Strategy Generated!")
        
        st.markdown(f"**Target Audience (ICP):** {data.get('target_audience', 'N/A')}")
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Landing Page Hero")
            lp = data.get("landing_page_copy", {})
            with st.container(border=True):
                st.markdown(f"# {lp.get('hero_headline', 'Headline')}")
                st.markdown(f"### {lp.get('hero_subheadline', 'Subheadline')}")
                st.button(lp.get('call_to_action', 'Click Here'), type="primary", use_container_width=True)
                
            st.write("")
            st.subheader("SEO Metadata")
            seo = data.get("seo_metadata", {})
            with st.container(border=True):
                st.text_input("Meta Title", value=seo.get("meta_title", ""))
                st.text_area("Meta Description", value=seo.get("meta_description", ""), height=100)

        with col2:
            st.subheader("Product Hunt Launch")
            ph = data.get("product_hunt_launch", {})
            with st.container(border=True):
                st.markdown(f"**Tagline:** {ph.get('tagline', '')}")
                st.markdown("**Maker Comment:**")
                st.info(ph.get("maker_comment", ""))
                
            st.write("")
            st.subheader("Email Announcement")
            email = data.get("launch_email", {})
            with st.container(border=True):
                st.markdown(f"**Subject:** `{email.get('subject_line', '')}`")
                st.markdown("**Body:**")
                st.write(email.get("email_body", ""))
