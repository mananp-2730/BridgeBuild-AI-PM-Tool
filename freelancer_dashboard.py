import streamlit as st
import json
import time

# ==========================================
# FREELANCER DASHBOARD RENDERER
# ==========================================
def render_freelancer_dashboard(supabase):
    st.title("The God Dashboard (Freelancer Mode)")
    st.markdown("### End-to-End Continuous Pipeline")
    st.caption("Bypass department queues. Upload your idea and watch the entire architecture build out in a single flow.")

    # --- 1. STATE MANAGEMENT ---
    # We use these flags to track how far down the waterfall the user has progressed.
    if "fl_stage" not in st.session_state:
        st.session_state.fl_stage = 0  # 0: Start, 1: Sales Done, 2: PM Done, 3: Eng Done
    
    if "fl_sales_data" not in st.session_state: st.session_state.fl_sales_data = None
    if "fl_pm_data" not in st.session_state: st.session_state.fl_pm_data = None
    if "fl_eng_data" not in st.session_state: st.session_state.fl_eng_data = None
    if "fl_input_text" not in st.session_state: st.session_state.fl_input_text = ""

    # --- RESET PIPELINE BUTTON ---
    col_head1, col_head2 = st.columns([4, 1])
    with col_head2:
        if st.button("🔄 Reset Pipeline", use_container_width=True):
            st.session_state.fl_stage = 0
            st.session_state.fl_sales_data = None
            st.session_state.fl_pm_data = None
            st.session_state.fl_eng_data = None
            st.rerun()

    st.divider()

    # ==========================================
    # STAGE 0: THE INTAKE (Always Visible)
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
            else:
                with st.spinner("Analyzing Market Feasibility..."):
                    time.sleep(1) # Placeholder for Gemini API Call
                    # Fake Data for UI testing
                    st.session_state.fl_sales_data = {"budget": "$15,000", "score": "Green (Highly Feasible)"}
                    st.session_state.fl_stage = 1
                    st.rerun()

    # ==========================================
    # STAGE 1: PM SCOPING (Unlocks after Intake)
    # ==========================================
    if st.session_state.fl_stage >= 1:
        st.write("⬇️") # Visual waterfall indicator
        with st.container(border=True):
            st.markdown("#### 2️⃣ Agile Scoping & User Stories")
            st.success(f"Feasibility Complete! Estimated Budget: {st.session_state.fl_sales_data.get('budget')}")
            
            if st.session_state.fl_stage == 1:
                if st.button("Generate Agile Epics & Stories", type="primary"):
                    with st.spinner("Writing Jira Tickets..."):
                        time.sleep(1) # Placeholder for Gemini API Call
                        st.session_state.fl_pm_data = {"epics": 4, "stories": 12}
                        st.session_state.fl_stage = 2
                        st.rerun()
            else:
                st.info(f"Generated {st.session_state.fl_pm_data.get('epics')} Epics and {st.session_state.fl_pm_data.get('stories')} User Stories.")

    # ==========================================
    # STAGE 2: ENGINEERING (Unlocks after PM)
    # ==========================================
    if st.session_state.fl_stage >= 2:
        st.write("⬇️")
        with st.container(border=True):
            st.markdown("#### 3️⃣ Technical Architecture")
            
            if st.session_state.fl_stage == 2:
                if st.button("Generate DB Schema & APIs", type="primary"):
                    with st.spinner("Architecting Database..."):
                        time.sleep(1) # Placeholder for Gemini API Call
                        st.session_state.fl_eng_data = {"status": "Complete"}
                        st.session_state.fl_stage = 3
                        st.rerun()
            else:
                st.success("Database Schema and API Routes generated successfully.")

    # ==========================================
    # STAGE 3: CLOUD DEPLOYMENT (Unlocks at the end)
    # ==========================================
    if st.session_state.fl_stage >= 3:
        st.write("⬇️")
        with st.container(border=True):
            st.markdown("#### 🚀 Zero-to-Repo Deployment")
            st.info("Pipeline Complete. Ready to provision cloud infrastructure.")
            
            col_d1, col_d2 = st.columns([2, 1])
            with col_d1:
                st.text_input("Repository Name", placeholder="e.g., solo-founder-app")
            with col_d2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Provision GitHub Repo", type="primary", use_container_width=True):
                    st.balloons()
                    st.success("Deployment triggered! (Integration coming in Step 3)")
