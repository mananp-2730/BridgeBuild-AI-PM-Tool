import streamlit as st
import json
import os
import tempfile
from google import genai
from google.genai import types
from utils import safe_parse_json
from github import Github

# ==========================================
# FREELANCER DASHBOARD RENDERER
# ==========================================
def render_freelancer_dashboard(supabase):
    st.title("The God Dashboard (Freelancer Mode)")
    st.markdown("### End-to-End Continuous Pipeline")
    st.caption("Bypass department queues. Upload your idea and watch the entire architecture build out in a single flow.")

    api_key = st.secrets.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    # --- 1. STATE MANAGEMENT ---
    if "fl_stage" not in st.session_state: st.session_state.fl_stage = 0 
    if "fl_sales_data" not in st.session_state: st.session_state.fl_sales_data = None
    if "fl_pm_data" not in st.session_state: st.session_state.fl_pm_data = None
    if "fl_eng_data" not in st.session_state: st.session_state.fl_eng_data = None
    if "fl_input_text" not in st.session_state: st.session_state.fl_input_text = ""

    # --- RESET PIPELINE BUTTON ---
    col_head1, col_head2 = st.columns([4, 1])
    with col_head2:
        if st.button("🔄 Reset Pipeline", use_container_width=True):
            for key in ["fl_stage", "fl_sales_data", "fl_pm_data", "fl_eng_data"]:
                st.session_state[key] = None if key != "fl_stage" else 0
            st.session_state.fl_input_text = ""
            st.rerun()

    st.divider()

    # ==========================================
    # STAGE 0: THE INTAKE (Sales Feasibility)
    # ==========================================
    with st.container(border=True):
        st.markdown("#### 1️⃣ Project Intake & Feasibility")
        
        fl_input = st.text_area(
            "What are we building today?", 
            value=st.session_state.fl_input_text, 
            height=100, 
            placeholder="e.g., I want to build a SaaS for dog walkers with real-time GPS tracking..."
        )
        st.session_state.fl_input_text = fl_input
        uploaded_file = st.file_uploader("Or Upload Audio/Transcript", type=["mp3", "wav", "txt", "pdf"], key="fl_uploader")

        if st.button("Generate Feasibility & Budget", type="primary"):
            if not fl_input and not uploaded_file:
                st.warning("Please provide a prompt or upload a file.")
            elif not client:
                st.error("Google API Key missing in secrets.toml!")
            else:
                with st.status("Analyzing Market Feasibility...", expanded=True) as status:
                    st.write("Extracting core business logic...")
                    
                    prompt_contents = []
                    if uploaded_file:
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)

                    instructions = """Analyze this software idea. Output ONLY valid JSON with these exact keys:
                    {"project_summary": "A clear 2-sentence summary", "budget_estimate_usd": "$10,000 - $15,000", "feasibility_score": "Green (Highly Feasible)", "deal_breakers": ["List of potential risks"]}"""
                    
                    prompt_contents.append(f"{instructions}\n\nClient Input: {fl_input}")

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json"),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file: client.files.delete(name=gemini_file.name)

                    parsed_data, err = safe_parse_json(response.text)
                    if err:
                        status.update(label="Error Parsing AI Output", state="error", expanded=True)
                        st.error(err)
                    else:
                        st.session_state.fl_sales_data = parsed_data
                        st.session_state.fl_stage = 1
                        status.update(label="Feasibility Complete!", state="complete", expanded=False)
                        st.rerun()

    # ==========================================
    # STAGE 1: PM SCOPING
    # ==========================================
    if st.session_state.fl_stage >= 1:
        st.write("⬇️") 
        with st.container(border=True):
            st.markdown("#### 2️⃣ Agile Scoping & User Stories")
            sales_data = st.session_state.fl_sales_data
            st.success(f"**Budget:** {sales_data.get('budget_estimate_usd', 'N/A')} | **Feasibility:** {sales_data.get('feasibility_score', 'N/A')}")
            st.caption(f"Summary: {sales_data.get('project_summary', 'N/A')}")
            
            if st.session_state.fl_stage == 1:
                if st.button("Generate Agile Epics & Stories", type="primary"):
                    with st.status("Writing Jira Tickets...", expanded=True) as status:
                        st.write("Translating executive summary into Agile requirements...")
                        
                        pm_prompt = f"""Based on this project summary, write Agile Epics and MVP User Stories. Output ONLY valid JSON matching this structure:
                        {{"epics": ["Epic 1: Auth", "Epic 2: Dashboard"], "user_stories": ["As a user, I want to...", "As an admin, I want to..."]}}
                        
                        Project Summary: {sales_data.get('project_summary', '')}"""

                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json"),
                            contents=[pm_prompt]
                        )
                        
                        parsed_data, err = safe_parse_json(response.text)
                        if err:
                            status.update(label="Error", state="error", expanded=True)
                            st.error(err)
                        else:
                            st.session_state.fl_pm_data = parsed_data
                            st.session_state.fl_stage = 2
                            status.update(label="Agile Scoping Complete!", state="complete", expanded=False)
                            st.rerun()
            else:
                pm_data = st.session_state.fl_pm_data
                st.info(f"Generated {len(pm_data.get('epics', []))} Epics and {len(pm_data.get('user_stories', []))} User Stories.")
                with st.expander("View Agile Scope"):
                    for epic in pm_data.get('epics', []): st.markdown(f"- **{epic}**")

    # ==========================================
    # STAGE 2: ENGINEERING 
    # ==========================================
    if st.session_state.fl_stage >= 2:
        st.write("⬇️")
        with st.container(border=True):
            st.markdown("#### 3️⃣ Technical Architecture")
            
            if st.session_state.fl_stage == 2:
                if st.button("Generate DB Schema & APIs", type="primary"):
                    with st.status("Architecting Database...", expanded=True) as status:
                        st.write("Designing PostgreSQL schema and endpoints based on PM Epics...")
                        
                        eng_prompt = f"""Act as a Lead Software Architect. Based on these Agile Epics, design the backend architecture.
                        Output ONLY valid JSON matching this EXACT structure:
                        {{
                            "system_architecture": "A brief overview of how the system works",
                            "tech_stack_recommendation": {{"frontend": "React", "backend": "Node.js", "database": "PostgreSQL"}},
                            "database_schema": [
                                {{"table_name": "users", "columns": ["id UUID PRIMARY KEY", "email VARCHAR"]}}
                            ]
                        }}
                        
                        Agile Epics: {st.session_state.fl_pm_data.get('epics', [])}"""

                        response = client.models.generate_content(
                            model="gemini-2.5-flash", 
                            config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"),
                            contents=[eng_prompt]
                        )
                        
                        parsed_data, err = safe_parse_json(response.text)
                        if err:
                            status.update(label="Error", state="error", expanded=True)
                            st.error(err)
                        else:
                            st.session_state.fl_eng_data = parsed_data
                            st.session_state.fl_stage = 3
                            status.update(label="Architecture Generated!", state="complete", expanded=False)
                            st.rerun()
            else:
                eng_data = st.session_state.fl_eng_data
                st.success("Database Schema and Architecture generated successfully.")
                with st.expander("View Database Tables"):
                    for table in eng_data.get('database_schema', []):
                        st.markdown(f"**Table: {table.get('table_name')}**")
                        for col in table.get('columns', []): st.caption(f"- {col}")

    # ==========================================
    # STAGE 3: CLOUD DEPLOYMENT (Coming in Step 3!)
    # ==========================================
    if st.session_state.fl_stage >= 3:
        st.write("⬇️")
        with st.container(border=True):
            st.markdown("#### Zero-to-Repo Deployment")
            st.info("Pipeline Complete. Your architecture is ready to be pushed to GitHub.")
            
            col_d1, col_d2 = st.columns([2, 1])
            with col_d1:
                st.text_input("Repository Name", placeholder="e.g., solo-founder-app", key="fl_repo_name")
            with col_d2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Provision GitHub Repo", type="primary", use_container_width=True):
                    st.balloons()
                    st.success("Data is ready! We will wire the GitHub API here in Step 3.")
