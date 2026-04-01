import streamlit as st
import json
from google import genai
from google.genai import types
from prompts import get_marketing_prompt, get_localization_prompt # <-- NEW IMPORT
from utils import clean_json_output, safe_parse_json

def render_marketing_dashboard(supabase):
    st.title("BridgeBuild AI - Marketing Studio")
    st.markdown("### Translate technical features into high-converting Go-To-Market copy.")

    api_key = st.secrets.get("GOOGLE_API_KEY")
    user_prefs = st.session_state.get("user_prefs", {})
    model_choice = user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")

    # --- 1. PROJECT SELECTOR ---
    st.markdown("#### Select Project for GTM Launch")
    try:
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

    # --- STATE MANAGEMENT ---
    if "active_marketing_data" not in st.session_state:
        st.session_state.active_marketing_data = None
    if "localized_marketing_data" not in st.session_state:
        st.session_state.localized_marketing_data = None
    if "target_region" not in st.session_state:
        st.session_state.target_region = "Global (English)"

    # --- 2. BASE GENERATION ENGINE ---
    if st.button("🚀 Generate Base GTM Strategy (English)", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                MARKETING_PROMPT = get_marketing_prompt()

                with st.status("Analyzing technical specs & generating copy...", expanded=True) as status:
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    project_context = f"PROJECT DATA:\n{selected_project.get('full_data', selected_project.get('summary'))}"
                    
                    st.write("Drafting Landing Page & SEO...")
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=MARKETING_PROMPT, 
                            temperature=0.7, 
                            response_mime_type="application/json"
                        ),
                        contents=[project_context]
                    )
                    
                    data, error_msg = safe_parse_json(response.text)
                    
                    if error_msg:
                        status.update(label="Generation Failed", state="error", expanded=True)
                        st.error(error_msg)
                        st.stop()
                    else:
                        status.update(label="Base Marketing Assets Ready!", state="complete", expanded=False)
                        st.session_state.active_marketing_data = data
                        st.session_state.localized_marketing_data = None # Reset localization if new base is generated

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # --- 3. GLOBAL EXPANSION ENGINE (LOCALIZATION) ---
    if st.session_state.active_marketing_data:
        st.write("")
        with st.expander("🌍 Global Expansion Engine (Localize Strategy)", expanded=True):
            st.markdown("Launch this product in a new international market. The AI will adapt the tone, culture, and SEO keywords.")
            
            target_region = st.selectbox(
                "Select Target Market:", 
                ["UAE (Arabic / AED)", "Japan (Japanese / JPY)", "Germany (German / EUR)", "Latin America (Spanish / MXN)", "France (French / EUR)", "India (Hindi / INR)"]
            )
            
            if st.button("🌐 Translate & Localize Campaign"):
                try:
                    client = genai.Client(api_key=api_key)
                    LOCALIZATION_PROMPT = get_localization_prompt()

                    with st.status(f"Localizing for {target_region}...", expanded=True) as status:
                        model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                        
                        # Feed the existing base GTM data to the AI
                        base_gtm_str = json.dumps(st.session_state.active_marketing_data)
                        localization_context = f"BASE GTM STRATEGY:\n{base_gtm_str}\n\nTARGET REGION: {target_region}"
                        
                        st.write("Adapting cultural tone and SEO metrics...")
                        response = client.models.generate_content(
                            model=model_id, 
                            config=types.GenerateContentConfig(
                                system_instruction=LOCALIZATION_PROMPT, 
                                temperature=0.7, 
                                response_mime_type="application/json"
                            ),
                            contents=[localization_context]
                        )
                        
                        loc_data, error_msg = safe_parse_json(response.text)
                        
                        if error_msg:
                            status.update(label="Localization Failed", state="error", expanded=True)
                            st.error(error_msg)
                        else:
                            status.update(label=f"Successfully Localized for {target_region}!", state="complete", expanded=False)
                            st.session_state.localized_marketing_data = loc_data
                            st.session_state.target_region = target_region
                except Exception as e:
                    st.error(f"An error occurred during localization: {str(e)}")

        st.divider()

        # --- 4. RENDER OUTPUT UI (WITH TABS) ---
        tab_names = ["🇺🇸 Base GTM (English)"]
        if st.session_state.localized_marketing_data:
            tab_names.append(f"🌍 Localized ({st.session_state.target_region})")
            
        tabs = st.tabs(tab_names)
        
        # TAB 1: Base English Render
        with tabs[0]:
            base_data = st.session_state.active_marketing_data
            st.markdown(f"**🎯 Target Audience (ICP):** {base_data.get('target_audience', 'N/A')}")
            st.write("")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Landing Page Hero")
                lp = base_data.get("landing_page_copy", {})
                with st.container(border=True):
                    st.markdown(f"# {lp.get('hero_headline', 'Headline')}")
                    st.markdown(f"### {lp.get('hero_subheadline', 'Subheadline')}")
                    st.button(lp.get('call_to_action', 'Click Here'), key="btn_base", type="primary", use_container_width=True)
                    
                st.write("")
                st.subheader("SEO Metadata")
                seo = base_data.get("seo_metadata", {})
                with st.container(border=True):
                    st.text_input("Meta Title", value=seo.get("meta_title", ""), key="seo_t_base")
                    st.text_area("Meta Description", value=seo.get("meta_description", ""), height=100, key="seo_d_base")

            with col2:
                st.subheader("Product Hunt Launch")
                ph = base_data.get("product_hunt_launch", {})
                with st.container(border=True):
                    st.markdown(f"**Tagline:** {ph.get('tagline', '')}")
                    st.markdown("**Maker Comment:**")
                    st.info(ph.get("maker_comment", ""))
                    
                st.write("")
                st.subheader("Email Announcement")
                email = base_data.get("launch_email", {})
                with st.container(border=True):
                    st.markdown(f"**Subject:** `{email.get('subject_line', '')}`")
                    st.markdown("**Body:**")
                    st.write(email.get("email_body", ""))
                    
        # TAB 2: Localized Render (If Generated)
        if st.session_state.localized_marketing_data and len(tabs) > 1:
            with tabs[1]:
                loc_data = st.session_state.localized_marketing_data
                st.info(f"**Cultural Adaptation Summary:** {loc_data.get('region_summary', 'N/A')}")
                st.write("")
                
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader("Localized Landing Page")
                    llp = loc_data.get("localized_landing_page", {})
                    with st.container(border=True):
                        st.markdown(f"# {llp.get('hero_headline', 'Headline')}")
                        st.markdown(f"### {llp.get('hero_subheadline', 'Subheadline')}")
                        st.button(llp.get('call_to_action', 'Click Here'), key="btn_loc", type="primary", use_container_width=True)
                        
                    st.write("")
                    st.subheader("Localized SEO Metadata")
                    lseo = loc_data.get("localized_seo", {})
                    with st.container(border=True):
                        st.text_input("Meta Title", value=lseo.get("meta_title", ""), key="seo_t_loc")
                        st.text_area("Meta Description", value=lseo.get("meta_description", ""), height=100, key="seo_d_loc")

                with col4:
                    st.subheader("Localized Email Announcement")
                    lemail = loc_data.get("localized_launch_email", {})
                    with st.container(border=True):
                        st.markdown(f"**Subject:** `{lemail.get('subject_line', '')}`")
                        st.markdown("**Body:**")
                        st.write(lemail.get("email_body", ""))
