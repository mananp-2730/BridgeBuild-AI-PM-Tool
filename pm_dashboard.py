import streamlit as st
import json
import urllib.parse
import tempfile
import os
from google import genai
from google.genai import types
from prompts import get_system_prompt
from utils import clean_json_output, generate_jira_format, convert_currency, create_pdf

def render_pm_dashboard(supabase):
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        
        with col_logo:
            st.image("Logo_bg_removed.png", width=40) 
            
        with col_text:
            st.markdown(
                """
                <h3 style='margin: 0; padding-top: 8px; padding-bottom: 10px; font-size: 18px; color: var(--text-color); font-weight: 600;'>
                    BridgeBuild AI
                </h3>
                """, 
                unsafe_allow_html=True
            )
        
        st.caption(f"Department: {st.session_state.get('user_role', 'Unknown').upper()}")

        api_key = st.secrets.get("GOOGLE_API_KEY")
        st.write("")
        
        if "user_prefs" not in st.session_state:
            try:
                user_id = st.session_state.user.id
                profile_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
                
                if profile_res.data:
                    st.session_state.user_prefs = profile_res.data[0]
                else:
                    default_prefs = {
                        "id": user_id, "currency": "USD ($)", 
                        "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)"
                    }
                    supabase.table("profiles").insert(default_prefs).execute()
                    st.session_state.user_prefs = default_prefs
            except Exception as e:
                st.session_state.user_prefs = {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)"}

        curr_opts = ["USD ($)", "INR (₹)"]
        rate_opts = ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"]
        model_opts = ["Gemini 1.5 Flash (Fast)", "Gemini 1.5 Pro (High Reasoning)"]

        curr_pref = st.session_state.user_prefs.get("currency", "USD ($)")
        curr_idx = curr_opts.index(curr_pref) if curr_pref in curr_opts else 0
        rate_pref = st.session_state.user_prefs.get("rate_standard", "US Agency ($150/hr)")
        rate_idx = rate_opts.index(rate_pref) if rate_pref in rate_opts else 0
        model_pref = st.session_state.user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")
        model_idx = model_opts.index(model_pref) if model_pref in model_opts else 0

        st.divider()
        st.header("Business Settings")
        
        currency = st.radio("Display Currency:", curr_opts, index=curr_idx)
        rate_type = st.selectbox("Rate Standard:", rate_opts, index=rate_idx)
        model_choice = st.radio("AI Model:", model_opts, index=model_idx)
        
        st.write("")
        st.subheader("Architectural Strategy")
        build_strategy = st.select_slider(
            "Project Focus:",
            options=["Speed (Low-Code/MVP)", "Balanced", "Scale (Enterprise/Microservices)"],
            value="Balanced"
        )
        st.write("")
        st.write("")
        st.divider()
        
        if st.button("Save Settings", use_container_width=True):
            new_prefs = {"currency": currency, "rate_standard": rate_type, "ai_model": model_choice}
            try:
                supabase.table("profiles").update(new_prefs).eq("id", st.session_state.user.id).execute()
                st.session_state.user_prefs.update(new_prefs)
                st.success("Settings saved successfully!")
            except Exception as e:
                st.error(f"Failed to save settings: {str(e)}")
                
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
            
        if st.button("Clear History"):
            try:
                supabase.table("tickets").delete().eq("user_id", st.session_state.user.id).execute()
                st.success("Database History Cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear history: {str(e)}")

    st.title("BridgeBuild AI")
    st.markdown("### Turn Sales Conversations into Engineering Tickets & Budgets")

    if st.button("Load Sample Email"):
        st.session_state.sales_input = "Client wants a mobile app for food delivery. Needs GPS tracking for drivers, a menu for customers, and a payment gateway. They have a budget of $15k."
    
    if "sales_input" not in st.session_state: st.session_state.sales_input = ""

    uploaded_file = st.file_uploader("Upload Meeting Audio or Transcript (.mp3, .wav, .txt, .pdf)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']: st.audio(uploaded_file)
            
    sales_input = st.text_area("Paste Text or Add Extra Context:", value=st.session_state.sales_input, height=150)

    if "active_ticket" not in st.session_state: st.session_state.active_ticket = None
    if "active_ticket_id" not in st.session_state: st.session_state.active_ticket_id = None

    if st.button("Generate Ticket & Budget"):
        if not api_key: st.error("System Error: AI Engine is currently offline.")
        elif not sales_input and not uploaded_file: st.warning("Please enter text or upload a file.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                SYSTEM_PROMPT = get_system_prompt(rate_type, build_strategy)
                loading_msg = "Consulting Engineering & Finance Teams..."
                
                # --- PREMIUM WAITING ROOM EXPERIENCE (PM) ---
                with st.status("Consulting Engineering & Finance Teams...", expanded=True) as status:
                    st.write("Parsing input and extracting requirements...")
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.write("Processing multi-modal audio/document file...")
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)
                    
                    st.write(f"Generating Architecture (Strategy: {build_strategy})...")
                    text_instruction = sales_input if sales_input else "Analyze this meeting recording/transcript."
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.0, response_mime_type="application/json"),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        st.write("Cleaning up temporary files...")
                        client.files.delete(name=gemini_file.name)
                    
                    st.write("Structuring Epics, Stories, and Budgets...")
                    cleaned_text = clean_json_output(response.text)
                    data = json.loads(cleaned_text)
                    
                    status.update(label="Agile Ticket Generated!", state="complete", expanded=False)
                st.session_state.active_ticket = data
                st.success("Analysis Complete!")

                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)

                new_ticket = {
                    "user_id": st.session_state.user.id, "summary": data.get("summary"), "cost": f"{fmt_low} - {fmt_high}",
                    "raw_cost": raw_cost, "complexity": data.get("complexity_score"), "time": data.get("development_time"), "full_data": response.text
                }
                db_res = supabase.table("tickets").insert(new_ticket).execute()
                st.session_state.active_ticket_id = db_res.data[0]['id']
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    if st.session_state.active_ticket:
        data = st.session_state.active_ticket
        raw_cost = data.get("budget_estimate_usd", "0-0")
        low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
        high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
        fmt_low = convert_currency(low_end, currency)
        fmt_high = convert_currency(high_end, currency)

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Complexity", data.get("complexity_score"))
        with col2: st.metric("Dev Time", data.get("development_time"))
        with col3: st.metric("Est. Budget", f"{fmt_low} - {fmt_high}")
        with col4: st.metric("Risks Detected", len(data.get("technical_risks", [])))

        st.divider()
        
        with st.expander("Engineering Ticket Summary", expanded=True): st.info(f"**Summary:** {data.get('summary')}")
            
        if data.get("ambiguity_flags"):
            with st.expander("PM Pre-Flight: Missing Context", expanded=False):
                for flag in data.get("ambiguity_flags", []): st.warning(f"{flag}")
                    
        if data.get("epic_sub_tasks") and len(data.get("epic_sub_tasks")) > 0:
            with st.expander("Epic Breakdown (Sub-Tasks)", expanded=True):
                for i, task in enumerate(data.get("epic_sub_tasks")):
                    st.markdown(f"**{i+1}. {task.get('task_name', 'Sub-Task')}**")
                    st.caption(f"Est. Time: {task.get('estimated_days', 'N/A')}")
                    st.markdown(f"> {task.get('description', '')}")
                    st.write("")
                    
        with st.expander("Phase 1: Core MVP", expanded=False):
            if "mvp_user_stories" in data:
                for item in data.get("mvp_user_stories", []):
                    st.markdown(f"**{item.get('story', 'User Story')}**")
                    for ac in item.get("acceptance_criteria", []): st.markdown(f"  * {ac}")
                    st.write("")
            else:
                for feat in data.get("mvp_features", []): st.markdown(f"- {feat}")
                    
        with st.expander("Phase 2: Future Enhancements", expanded=False):
            p2_raw = data.get("phase_2_budget_usd", "0-0")
            p2_low = p2_raw.split("-")[0] if "-" in p2_raw else p2_raw
            p2_high = p2_raw.split("-")[1] if "-" in p2_raw else p2_raw
            p2_fmt_low = convert_currency(p2_low, currency)
            p2_fmt_high = convert_currency(p2_high, currency)
            
            st.caption(f"**Est. Extra Time:** {data.get('phase_2_time', 'N/A')} | **Est. Extra Budget:** {p2_fmt_low} - {p2_fmt_high}")
            for feat in data.get("phase_2_features", []): st.markdown(f"- {feat}")
                
        with st.expander("Technical Risks", expanded=False):
            for risk in data.get("technical_risks", []): st.warning(f"- {risk}")
                
        with st.expander("Suggested Tech Stack", expanded=False):
            st.code("\n".join(data.get("suggested_stack", [])), language="bash")
            
        with st.expander("Data Schema", expanded=False):
            for entity in data.get("primary_entities", []): st.success(f"🆔 {entity}")

        with st.expander("Architecture & Flowchart", expanded=False):
            if data.get("mermaid_diagram"): st.markdown(f"```mermaid\n{data.get('mermaid_diagram')}\n```")
            else: st.info("No architecture diagram generated.")

        st.divider()
        col_action1, col_action2 = st.columns([1, 1], gap="medium")
        
        with col_action1:
            st.markdown("#### Export PDF Reports")
            st.download_button("Download Detailed Ticket (Engineering)", data=create_pdf(data, currency, ticket_type="detailed"), file_name="bridgebuild_detailed_ticket.pdf", mime="application/pdf", use_container_width=True)
            st.download_button("Download Brief Summary (Sales / Client)", data=create_pdf(data, currency, ticket_type="brief"), file_name="bridgebuild_brief_summary.pdf", mime="application/pdf", use_container_width=True)
        
        with col_action2:
            st.markdown("#### Share with Stakeholders")
            ticket_name = data.get('ticket_name', data.get('summary', 'New Project'))[:50]
            
            eng_body = f"Hello Engineering Team,\n\nPlease review the scoped Agile requirements...\n\n-> SUMMARY:\n{data.get('summary', 'N/A')}\n\nBest,\nProduct Management"
            eng_mailto = f"mailto:?subject={urllib.parse.quote(f'Eng Ticket: {ticket_name}')}&body={urllib.parse.quote(eng_body)}"
            
            sales_body = f"Hello Sales Team,\n\nGreat news—we have completed the initial feasibility scoping...\n\nBest,\nProduct Management"
            sales_mailto = f"mailto:?subject={urllib.parse.quote(f'Sales Scoping: {ticket_name}')}&body={urllib.parse.quote(sales_body)}"
            
            st.markdown(f"""
                <a href="{eng_mailto}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background-color: #012169; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-bottom: 10px;">Email to Engineering</button></a>
                <a href="{sales_mailto}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background-color: #2E7D32; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer;">Email to Sales</button></a>
                """, unsafe_allow_html=True)
            
            with st.expander("View Jira / Confluence Markup", expanded=False):
                st.code(generate_jira_format(data, currency), language="jira")
                
        refine_query = st.chat_input("E.g., Add a risk about third-party API rate limits...")
        if refine_query:
            if not api_key: st.error("API Key missing.")
            else:
                with st.spinner("AI is updating the ticket..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                        update_prompt = f"You are a Technical Product Manager. Update the JSON ticket based on request.\nCURRENT TICKET:\n{json.dumps(data)}\nUSER REQUEST:\n{refine_query}"
                        
                        update_response = client.models.generate_content(
                            model=model_id, 
                            config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"),
                            contents=update_prompt
                        )
                        
                        updated_data = json.loads(clean_json_output(update_response.text))
                        st.session_state.active_ticket = updated_data
                        
                        if st.session_state.active_ticket_id:
                            supabase.table("tickets").update({"summary": updated_data.get("summary"), "complexity": updated_data.get("complexity_score"), "time": updated_data.get("development_time"), "full_data": update_response.text}).eq("id", st.session_state.active_ticket_id).execute()
                            
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Failed to refine: {str(e)}")

    st.divider()
    st.subheader("Saved Tickets History")
    try:
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        if saved_tickets:
            for i, item in enumerate(saved_tickets):
                with st.expander(f"Ticket: {item['summary'][:60]}..."):
                    past_data = json.loads(item['full_data'])
                    hist_btn_col1, hist_btn_col2, hist_btn_col3 = st.columns([2, 2, 1])
                    
                    with hist_btn_col1:
                        st.download_button(label="Download PDF", data=create_pdf(past_data, currency, ticket_type="detailed"), file_name=f"ticket_{item['id'][:8]}.pdf", mime="application/pdf", key=f"hist_pdf_{item['id']}", use_container_width=True)
                    with hist_btn_col3:
                        if st.button("Delete", key=f"del_{item['id']}", use_container_width=True):
                            try:
                                supabase.table("tickets").delete().eq("id", item['id']).execute()
                                st.rerun() 
                            except Exception as e:
                                st.error(f"Failed to delete ticket: {str(e)}")
                    st.write("") 
                    with st.expander("🎫 View Jira / Confluence Markup", expanded=False):
                        st.code(generate_jira_format(past_data, currency), language="jira")
        else:
            st.info("No saved tickets yet. Generate your first one above!")
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
    
    st.markdown("---")
    footer_html = """
    <div style='text-align: center; color: #666666; font-size: 0.8em; font-family: sans-serif;'>
        <p>Built by <a href='https://github.com/mananp-2730' target='_blank' style='text-decoration: none; color: #0366d6;'>Manan Patel</a></p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
