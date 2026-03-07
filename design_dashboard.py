import streamlit as st
import json
import os
import tempfile
from google import genai
from google.genai import types
from prompts import get_design_prompt
from utils import clean_json_output
import re

def render_design_dashboard(supabase):

    st.title("BridgeBuild AI - UX/UI Design Intake")
    st.markdown("### Transform messy client ideas into structured user flows and screen layouts.")

    uploaded_file = st.file_uploader("Upload Client Audio/Notes (.mp3, .wav)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']:
            st.audio(uploaded_file)
            
    design_input = st.text_area("Or Paste Notes:", height=150, placeholder="Example: Client wants a fitness app where users can track workouts and share with friends. Needs to feel modern and energetic.")

    api_key = st.secrets.get("GOOGLE_API_KEY")
    model_choice = st.session_state.get("user_prefs", {}).get("ai_model", "Gemini 1.5 Flash (Fast)")

    if st.button("Generate Design Architecture", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline. Please contact support.")
        elif not design_input and not uploaded_file:
            st.warning("Please enter text or upload a file to proceed.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                DESIGN_PROMPT = get_design_prompt()

                with st.spinner("Mapping user journeys and rendering UI components..."):
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.toast("Processing file...", icon="⏳")
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)
                    
                    text_instruction = design_input if design_input else "Extract UX/UI design requirements from this request."
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=DESIGN_PROMPT,
                            temperature=0.4, # Slightly higher temperature for more creative design choices!
                            response_mime_type="application/json"
                        ),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        client.files.delete(name=gemini_file.name)
                    
                    cleaned_text = clean_json_output(response.text)
                    data = json.loads(cleaned_text)

                # --- 1. RENDER THE DESIGN UI ---
                st.write("")
                st.success("Design Architecture Generated!")
                
                theme = data.get("design_theme", {})
                vibe = theme.get("vibe", "Modern & Clean")
                raw_color_text = theme.get("primary_color_suggestion", "#012169")
                
                # --- SAFETY NET: Extract just the hex code using regex ---
                match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', raw_color_text)
                safe_hex = match.group(0) if match else "#012169"
                
                # Render a visual color block (Backticks removed, text shadow added for readability!)
                st.markdown(f"### The Vibe: {vibe}")
                st.markdown(f"**Suggested Primary Color:** <span style='background-color: {safe_hex}; color: white; padding: 6px 10px; border-radius: 6px; text-shadow: 1px 1px 2px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.2);'>{raw_color_text}</span>", unsafe_allow_html=True)                
                st.info(f"**Project Vision:** {data.get('project_vision')}")
                st.write(f"**Target Audience:** {data.get('target_audience')}")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Core User Flows")
                    for flow in data.get("core_user_flows", []):
                        with st.expander(f"Flow: {flow.get('flow_name', 'User Flow')}"):
                            for step in flow.get("steps", []):
                                st.markdown(f"- {step}")
                                
                    st.write("")
                    st.subheader("UI Component Library")
                    for comp in data.get("ui_components_needed", []):
                        st.markdown(f"- `{comp}`")

                with col2:
                    st.subheader("Key Screens & Layouts")
                    for screen in data.get("key_screens", []):
                        with st.container(border=True):
                            st.markdown(f"**{screen.get('screen_name', 'Screen')}**")
                            for elem in screen.get("core_elements", []):
                                st.caption(f"🔹 {elem}")
                                
                    st.write("")
                    st.subheader("Accessibility (a11y)")
                    for a11y in data.get("accessibility_a11y", []):
                        st.success(f"✓ {a11y}")

                # --- 2. SAVE TO SUPABASE ---
                # We map design data into the standard tickets table safely
                new_ticket = {
                    "user_id": st.session_state.user.id,
                    "summary": data.get("project_vision", "Design Architecture")[:200],
                    "cost": "N/A (Design Phase)",
                    "raw_cost": "0-0",
                    "complexity": "UI/UX Scoping", 
                    "time": "TBD",
                    "full_data": response.text
                }
                supabase.table("tickets").insert(new_ticket).execute()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # --- 3. DESIGN HISTORY SECTION ---
    st.divider()
    st.subheader("Saved Design Architectures")
    
    try:
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).eq("complexity", "UI/UX Scoping").order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        if saved_tickets:
            for item in saved_tickets:
                with st.expander(f"Design: {item['summary'][:60]}..."):
                    past_data = json.loads(item['full_data'])
                    
                    theme = past_data.get("design_theme", {})
                    st.markdown(f"**Vibe:** {theme.get('vibe', 'N/A')} | **Color:** {theme.get('primary_color_suggestion', 'N/A')}")
                    
                    col_hf1, col_hf2 = st.columns(2)
                    with col_hf1:
                        st.markdown("**Core Screens:**")
                        for screen in past_data.get("key_screens", []):
                            st.caption(f"- {screen.get('screen_name')}")
                    with col_hf2:
                        st.markdown("**Key UI Components:**")
                        for comp in past_data.get("ui_components_needed", [])[:4]: # Show first 4
                            st.caption(f"- {comp}")
                            
                    st.write("")
                    if st.button("Delete Concept", key=f"del_design_{item['id']}", use_container_width=True):
                        supabase.table("tickets").delete().eq("id", item['id']).execute()
                        st.rerun() 
        else:
            st.info("No saved design concepts yet. Start ideating above!")
            
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
