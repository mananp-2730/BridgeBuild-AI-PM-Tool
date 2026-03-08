import streamlit as st
import json
import os
import tempfile
from google import genai
from google.genai import types
from prompts import get_engineering_prompt
from utils import clean_json_output

def render_engineering_dashboard(supabase):
    # 1. Engineering-Specific Sidebar Tools
    with st.sidebar:
        st.markdown("#### DevOps Settings")
        cloud_target = st.selectbox("Deployment Target:", ["AWS (Enterprise)", "Google Cloud Platform", "Vercel + Supabase", "Self-Hosted / Docker"])

    # 2. Pull from Global Settings
    user_prefs = st.session_state.get("user_prefs", {})
    model_choice = user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")
    api_key = st.secrets.get("GOOGLE_API_KEY")

    st.title("BridgeBuild AI - Engineering Terminal")
    st.markdown("### Translate requirements into DB schemas, APIs, and CI/CD pipelines.")

    uploaded_file = st.file_uploader("Upload Tech Specs / Audio (.mp3, .wav, .txt, .pdf)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']:
            st.audio(uploaded_file)
            
    eng_input = st.text_area("Or Paste Raw Requirements:", height=150, placeholder="Example: We need a backend for a food delivery app. Drivers need to update location in real-time, users place orders, and restaurants accept them.")

    if st.button("Generate Technical Architecture", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline.")
        elif not eng_input and not uploaded_file:
            st.warning("Please enter text or upload a file to proceed.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                ENG_PROMPT = get_engineering_prompt()

                # --- PREMIUM WAITING ROOM EXPERIENCE ---
                with st.status("Booting up Engineering Architecture...", expanded=True) as status:
                    st.write("Analyzing technical constraints...")
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.write("Ingesting multi-modal requirements...")
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)
                    
                    st.write(f"Designing system for {cloud_target} deployment...")
                    text_instruction = f"{eng_input}\nTarget Deployment: {cloud_target}" if eng_input else f"Extract engineering requirements for {cloud_target}."
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=ENG_PROMPT,
                            temperature=0.1, # Very low temperature for strict, predictable engineering outputs
                            response_mime_type="application/json"
                        ),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        st.write("Cleaning up workspace...")
                        client.files.delete(name=gemini_file.name)
                    
                    st.write("Mapping database schemas and API endpoints...")
                    cleaned_text = clean_json_output(response.text)
                    data = json.loads(cleaned_text)
                    
                    status.update(label="System Architecture Compiled!", state="complete", expanded=False)

                # --- 1. RENDER THE ENGINEERING UI ---
                st.write("")
                st.success("Technical Execution Plan Ready")
                
                st.markdown("### System Architecture")
                st.info(data.get("system_architecture", "No architecture overview provided."))
                
                st.divider()
                
                col_tech1, col_tech2 = st.columns(2)
                tech_stack = data.get("tech_stack_recommendation", {})
                with col_tech1:
                    st.markdown("**Frontend:**")
                    st.code(tech_stack.get("frontend", "N/A"), language="bash")
                    st.markdown("**Backend:**")
                    st.code(tech_stack.get("backend", "N/A"), language="bash")
                with col_tech2:
                    st.markdown("**Database:**")
                    st.code(tech_stack.get("database", "N/A"), language="bash")
                    st.markdown("**Infrastructure:**")
                    st.code(tech_stack.get("infrastructure", "N/A"), language="bash")
                
                st.divider()
                
                col_schema, col_api = st.columns(2)
                
                with col_schema:
                    st.subheader("Database Schema")
                    for table in data.get("database_schema", []):
                        with st.expander(f"Table: {table.get('table_name', 'Unknown')}"):
                            st.caption(f"**Relations:** {table.get('relationships', 'None')}")
                            st.markdown("**Columns:**")
                            for col in table.get("columns", []):
                                st.markdown(f"- `{col}`")
                                
                with col_api:
                    st.subheader("API Endpoints")
                    for api in data.get("api_endpoints", []):
                        method = api.get('method', 'GET')
                        route = api.get('route', '/route')
                        
                        # Color code the methods for visual flair
                        color = "green" if method == "GET" else "blue" if method == "POST" else "orange" if method == "PUT" else "red"
                        
                        st.markdown(f"**:{color}[[{method}]]** `{route}`")
                        st.caption(f"↳ {api.get('purpose', 'No description.')}")
                        st.write("")
                
                st.divider()
                
                st.subheader("Security & CI/CD")
                st.markdown(f"**Deployment Pipeline:** {data.get('ci_cd_pipeline', 'Standard deployment.')}")
                for sec in data.get("security_and_compliance", []):
                    st.warning(f"🔒 {sec}")

                # --- 2. SAVE TO SUPABASE ---
                new_ticket = {
                    "user_id": st.session_state.user.id,
                    "summary": data.get("system_architecture", "Technical Architecture")[:200],
                    "cost": "N/A (Engineering Phase)",
                    "raw_cost": "0-0",
                    "complexity": "Engineering Architecture", 
                    "time": "TBD",
                    "full_data": response.text
                }
                supabase.table("tickets").insert(new_ticket).execute()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # --- 3. ENGINEERING HISTORY SECTION ---
    st.divider()
    st.subheader("Saved Architecture Schemas")
    
    try:
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).eq("complexity", "Engineering Architecture").order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        if saved_tickets:
            for item in saved_tickets:
                with st.expander(f"Arch: {item['summary'][:60]}..."):
                    past_data = json.loads(item['full_data'])
                    
                    st.markdown(f"**Pipeline:** {past_data.get('ci_cd_pipeline', 'N/A')}")
                    
                    col_hf1, col_hf2 = st.columns(2)
                    with col_hf1:
                        st.markdown("**Core Tables:**")
                        for table in past_data.get("database_schema", []):
                            st.caption(f"- `{table.get('table_name')}`")
                    with col_hf2:
                        st.markdown("**Key Routes:**")
                        for api in past_data.get("api_endpoints", [])[:3]: # Show first 3
                            st.caption(f"- {api.get('method')} `{api.get('route')}`")
                            
                    st.write("")
                    
                    # 3. Delete Action with our Saturday Guardrail!
                    with st.popover("Delete Schema", use_container_width=True):
                        st.warning("Are you sure? This cannot be undone.")
                        if st.button("Yes, Delete Forever", key=f"confirm_del_eng_{item['id']}", type="primary"):
                            try:
                                supabase.table("tickets").delete().eq("id", item['id']).execute()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {str(e)}")
        else:
            st.info("No saved architectures yet. Initialize a build above!")
            
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
