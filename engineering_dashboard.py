import streamlit as st
import json
import os
import tempfile
import io
import csv
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types
from prompts import get_engineering_prompt
from utils import clean_json_output, safe_parse_json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ==========================================
# LOCALIZED ENGINEERING PDF ENGINE
# ==========================================
def _safe_text(text):
    return str(text).replace("₹", "INR ").encode('ascii', 'ignore').decode('ascii')

def _draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=11, line_height=14):
    c.setFont(font_name, font_size)
    words = _safe_text(text).split(' ')
    line = ""
    for word in words:
        if c.stringWidth(line + word + " ", font_name, font_size) < max_width:
            line += word + " "
        else:
            c.drawString(x, y, line.strip())
            y -= line_height
            line = word + " "
    if line:
        c.drawString(x, y, line.strip())
        y -= line_height
    return y

def _check_page_break(c, current_y, height, threshold=100):
    if current_y < threshold:
        c.showPage()
        return height - 50
    return current_y

def _draw_header(c, width, height, title):
    c.setFillColorRGB(0.2, 0.2, 0.2) 
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 60, title)
    
    ist = timezone(timedelta(hours=5, minutes=30))
    date_str = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, _safe_text(f"Generated on: {date_str} | BridgeBuild AI"))
    if os.path.exists("Logo_bg_removed.png"):
        c.drawImage("Logo_bg_removed.png", width - 100, height - 90, width=80, height=80, mask='auto')

def generate_local_eng_pdf(ticket_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    _draw_header(c, width, height, "Technical Architecture Report")
    y = height - 140
    c.setFillColor(colors.black)
    
    y = _draw_wrapped_text(c, "System Architecture:", 40, y, 500, "Helvetica-Bold", 14)
    y -= 5
    y = _draw_wrapped_text(c, ticket_data.get('system_architecture', 'N/A'), 40, y, 500, "Helvetica", 11)
    y -= 15

    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(40, y, _safe_text("Tech Stack Recommendation"))
    y -= 20
    c.setFillColor(colors.black)
    
    tech_stack = ticket_data.get("tech_stack_recommendation", {})
    y = _draw_wrapped_text(c, f"Frontend: {tech_stack.get('frontend', 'N/A')}", 40, y, 500, "Helvetica", 11)
    y = _draw_wrapped_text(c, f"Backend: {tech_stack.get('backend', 'N/A')}", 40, y, 500, "Helvetica", 11)
    y = _draw_wrapped_text(c, f"Database: {tech_stack.get('database', 'N/A')}", 40, y, 500, "Helvetica", 11)
    y = _draw_wrapped_text(c, f"Infrastructure: {tech_stack.get('infrastructure', 'N/A')}", 40, y, 500, "Helvetica", 11)
    y -= 15
    
    integrations = ticket_data.get("third_party_integrations", [])
    if integrations:
        y = _check_page_break(c, y, height)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(40, y, _safe_text("3rd Party Integrations"))
        y -= 20
        c.setFillColor(colors.black)
        for integration in integrations:
            y = _check_page_break(c, y, height)
            c.drawString(50, y, "🔌")
            y = _draw_wrapped_text(c, integration, 65, y, 460, "Helvetica", 10)
        y -= 5

    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(40, y, _safe_text("Database Schema"))
    y -= 20
    c.setFillColor(colors.black)
    
    for table in ticket_data.get("database_schema", []):
        y = _check_page_break(c, y, height)
        y = _draw_wrapped_text(c, f"Table: {table.get('table_name', 'Unknown')}", 40, y, 480, "Helvetica-Bold", 11)
        for col in table.get("columns", []):
            y = _check_page_break(c, y, height)
            c.drawString(50, y, "-")
            y = _draw_wrapped_text(c, col, 60, y, 460, "Helvetica", 10)
        y -= 5

    y -= 10
    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(40, y, _safe_text("API Endpoints"))
    y -= 20
    c.setFillColor(colors.black)
    
    for api in ticket_data.get("api_endpoints", []):
        y = _check_page_break(c, y, height)
        method_route = f"[{api.get('method', 'GET')}] {api.get('route', '/route')}"
        y = _draw_wrapped_text(c, method_route, 40, y, 480, "Helvetica-Bold", 11)
        y = _draw_wrapped_text(c, f"Purpose: {api.get('purpose', 'N/A')}", 60, y, 460, "Helvetica", 10)
        y -= 5

    y -= 10
    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(40, y, _safe_text("Security & CI/CD"))
    y -= 20
    c.setFillColor(colors.black)
    y = _draw_wrapped_text(c, f"Pipeline: {ticket_data.get('ci_cd_pipeline', 'N/A')}", 40, y, 500, "Helvetica", 11)
    y -= 5
    for sec in ticket_data.get("security_and_compliance", []):
        y = _check_page_break(c, y, height)
        c.drawString(45, y, "*")
        y = _draw_wrapped_text(c, sec, 60, y, 480, "Helvetica", 10)

    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# ENGINEERING CSV EXPORTER ENGINE
# ==========================================
def generate_engineering_csv(ticket_data):
    """Converts DB Schema and API Endpoints into a developer-friendly CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["--- DATABASE SCHEMA ---", "", "", ""])
    writer.writerow(["Table Name", "Columns", "Relationships", "Type"])
    
    for table in ticket_data.get("database_schema", []):
        table_name = table.get("table_name", "Unknown")
        relationships = table.get("relationships", "None")
        columns = "\n".join([f"- {col}" for col in table.get("columns", [])])
        writer.writerow([table_name, columns, relationships, "Database Table"])
        
    writer.writerow([]) 
    
    writer.writerow(["--- API ROUTING ---", "", "", ""])
    writer.writerow(["Method", "Route", "Purpose", "Type"])
    
    for api in ticket_data.get("api_endpoints", []):
        method = api.get("method", "GET")
        route = api.get("route", "/")
        purpose = api.get("purpose", "No description")
        writer.writerow([method, route, purpose, "API Endpoint"])
        
    return output.getvalue().encode('utf-8')

# ==========================================
# ENGINEERING DASHBOARD RENDERER
# ==========================================
def render_engineering_dashboard(supabase):

    with st.sidebar:
        st.markdown("#### DevOps Settings")
        cloud_target = st.selectbox("Deployment Target:", ["AWS (Enterprise)", "Google Cloud Platform", "Vercel + Supabase", "Self-Hosted / Docker"])
        
        st.divider()
        st.markdown("#### Company Context Engine")
        st.caption("Force the AI to follow your specific internal coding standards.")
        company_guidelines = st.text_area(
            "Global Engineering Guidelines", 
            placeholder="e.g., We ONLY use PostgreSQL. Primary keys must be UUIDs. Backend must be Node.js REST API. No GraphQL.",
            height=150
        )

    user_prefs = st.session_state.get("user_prefs", {})
    model_choice = user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")
    api_key = st.secrets.get("GOOGLE_API_KEY")

    st.title("BridgeBuild AI - Engineering Terminal")
    st.markdown("### Translate requirements into DB schemas, APIs, and CI/CD pipelines.")

    if "eng_input" not in st.session_state: 
        st.session_state.eng_input = ""

    if "active_eng_ticket" not in st.session_state: 
        st.session_state.active_eng_ticket = None
    if "active_eng_ticket_id" not in st.session_state: 
        st.session_state.active_eng_ticket_id = None
    if "inherited_frontend" not in st.session_state:
        st.session_state.inherited_frontend = None

    # ==========================================
    # INCOMING QUEUE (INBOX)
    # ==========================================
    try:
        inbox_res = supabase.table("tickets").select("*").eq("status", "Awaiting Tech Architecture").eq("target_department", "Engineering").order("created_at", desc=True).execute()
        inbox_tickets = inbox_res.data
        
        if inbox_tickets:
            st.info(f"**INCOMING:** You have {len(inbox_tickets)} approved project(s) waiting for Technical Architecture!")
            for item in inbox_tickets:
                with st.expander(f"Incoming Ticket: {item['summary'][:60]}..."):
                    try:
                        prev_data = json.loads(item['full_data'])
                    except:
                        prev_data = {}
                        
                    st.write(f"**Budget Info:** {item['cost']} | **Complexity:** {item['complexity']}")
                    
                    if st.button("Accept & Load into Terminal", key=f"accept_{item['id']}", type="primary"):
                        supabase.table("tickets").update({"status": "Accepted by Engineering"}).eq("id", item['id']).execute()
                        
                        injection_text = f"HANDOFF CONTEXT:\nProject Summary: {prev_data.get('summary', prev_data.get('project_vision', item['summary']))}\n"
                        
                        if "mvp_user_stories" in prev_data:
                            injection_text += "User Stories to Build:\n"
                            for story in prev_data.get("mvp_user_stories", []):
                                injection_text += f"- {story.get('story')}\n"
                                
                        if "key_screens" in prev_data:
                            injection_text += "Design Screens to Support:\n"
                            for screen in prev_data.get("key_screens", []):
                                injection_text += f"- {screen.get('screen_name')}\n"
                                
                        # --- CATCH THE GENERATED FRONTEND CODE ---
                        if "generated_frontend_code" in prev_data:
                            st.session_state.inherited_frontend = prev_data["generated_frontend_code"]
                            injection_text += "\n[NOTE: Frontend React code has already been generated by the Design team. Focus strictly on Backend logic, Database Architecture, and API schemas.]\n"
                        else:
                            st.session_state.inherited_frontend = None
                                
                        st.session_state.eng_input = injection_text
                        st.rerun()
            st.divider()
    except Exception as e:
        st.warning(f"Could not load Inbox: {str(e)}")

    # ==========================================
    # GENERATOR UI
    # ==========================================
    uploaded_file = st.file_uploader("Upload Tech Specs / Audio (.mp3, .wav, .txt, .pdf)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']:
            st.audio(uploaded_file)
            
    eng_input = st.text_area("Paste Raw Requirements or Review Context:", value=st.session_state.eng_input, height=150, placeholder="Example: We need a backend for a food delivery app. Drivers need to update location in real-time, users place orders, and restaurants accept them.")

    if st.button("Generate Technical Architecture", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline.")
        elif not eng_input and not uploaded_file:
            st.warning("Please enter text or upload a file to proceed.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                ENG_PROMPT = get_engineering_prompt()

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
                    
                    text_instruction = ""
                    if company_guidelines.strip():
                        text_instruction += f"CRITICAL OVERRIDE - COMPANY GUIDELINES:\nYou must strictly adhere to the following internal coding standards and rules when designing the database, APIs, and tech stack:\n{company_guidelines}\n\n"
                    
                    text_instruction += f"PROJECT REQUIREMENTS:\n{eng_input}\nTarget Deployment: {cloud_target}" if eng_input else f"Extract engineering requirements for {cloud_target}."
                    
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=ENG_PROMPT,
                            temperature=0.1, 
                            response_mime_type="application/json"
                        ),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        st.write("Cleaning up workspace...")
                        client.files.delete(name=gemini_file.name)
                    
                    st.write("Mapping database schemas and API endpoints...")
                    data, error_msg = safe_parse_json(response.text)
                    
                    if error_msg:
                        status.update(label="Architecture Failed", state="error", expanded=True)
                        st.error(error_msg)
                        st.stop()
                    else:
                        status.update(label="System Architecture Compiled!", state="complete", expanded=False)
                        st.session_state.active_eng_ticket = data

                # SAVE TO SUPABASE
                new_ticket = {
                    "user_id": st.session_state.user.id,
                    "summary": data.get("system_architecture", "Technical Architecture")[:200],
                    "cost": "N/A (Engineering Phase)",
                    "raw_cost": "0-0",
                    "complexity": "Engineering Architecture", 
                    "time": "TBD",
                    "full_data": response.text,
                    "status": "Draft",
                    "target_department": "None"
                }
                db_res = supabase.table("tickets").insert(new_ticket).execute()
                st.session_state.active_eng_ticket_id = db_res.data[0]['id']
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # ==========================================
    # RENDER THE ACTIVE ENGINEERING UI
    # ==========================================
    if st.session_state.active_eng_ticket:
        data = st.session_state.active_eng_ticket
        
        st.write("")
        st.success("Technical Execution Plan Ready")
        
        st.markdown("### System Architecture")
        st.info(data.get("system_architecture", "No architecture overview provided."))
        
        st.divider()
        
        col_tech1, col_tech2 = st.columns(2)
        tech_stack = data.get("tech_stack_recommendation", {})
        with col_tech1:
            with st.container(border=True):
                st.caption("FRONTEND")
                st.markdown(f"**{tech_stack.get('frontend', 'N/A')}**")
            with st.container(border=True):
                st.caption("BACKEND")
                st.markdown(f"**{tech_stack.get('backend', 'N/A')}**")
        with col_tech2:
            with st.container(border=True):
                st.caption("DATABASE")
                st.markdown(f"**{tech_stack.get('database', 'N/A')}**")
            with st.container(border=True):
                st.caption("INFRASTRUCTURE")
                st.markdown(f"**{tech_stack.get('infrastructure', 'N/A')}**")
                
        integrations = data.get("third_party_integrations", [])
        if integrations:
            st.write("")
            st.markdown("#### Required Third-Party Integrations")
            integrations_html = ""
            for integration in integrations:
                integrations_html += f"<span style='background-color: #334155; color: white; padding: 6px 12px; border-radius: 4px; margin-right: 8px; margin-bottom: 8px; display: inline-block; font-size: 13px; font-weight: bold;'>{integration}</span>"
            st.markdown(integrations_html, unsafe_allow_html=True)
            
        # ==========================================
        # NEW: RENDER INHERITED FRONTEND CODE
        # ==========================================
        if st.session_state.get("inherited_frontend"):
            st.divider()
            st.subheader("🎨 Inherited Frontend Code (From Design)")
            code_payload = st.session_state.inherited_frontend
            st.info(f"**Styling Guide:** {code_payload.get('global_styles_summary', 'Tailwind CSS classes applied.')}")
            
            for comp in code_payload.get("generated_components", []):
                with st.expander(f"📦 {comp.get('component_name', 'Component')}"):
                    st.caption(comp.get('description', ''))
                    st.code(comp.get('code', '// Code missing'), language="jsx")
        
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
                
                color = "green" if method == "GET" else "blue" if method == "POST" else "orange" if method == "PUT" else "red"
                st.markdown(f"**:{color}[[{method}]]** `{route}`")
                st.caption(f"↳ {api.get('purpose', 'No description.')}")
                st.write("")
        
        st.divider()
        
        st.subheader("Security & CI/CD")
        st.markdown(f"**Deployment Pipeline:** {data.get('ci_cd_pipeline', 'Standard deployment.')}")
        for sec in data.get("security_and_compliance", []):
            st.warning(f"🔒 {sec}")

        st.divider()
        col_action1, col_action2 = st.columns([1, 1], gap="medium")
        
        with col_action1:
            st.markdown("#### Export Technical Specs")
            st.download_button(
                "Download Engineering PDF", 
                data=generate_local_eng_pdf(data), 
                file_name="bridgebuild_technical_architecture.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
            st.download_button(
                "Download CSV (DB & API Schema)", 
                data=generate_engineering_csv(data), 
                file_name="engineering_schema_export.csv", 
                mime="text/csv", 
                use_container_width=True
            )
            
        with col_action2:
            st.markdown("#### Share with Dev Team")
            
            eng_body = f"Hello Dev Team,\n\nPlease review the generated System Architecture for our upcoming build.\n\n"
            eng_body += f"-> ARCHITECTURE OVERVIEW:\n{data.get('system_architecture', 'N/A')}\n\n"
            
            eng_body += f"-> TECH STACK:\n"
            eng_body += f"  - Frontend: {tech_stack.get('frontend', 'N/A')}\n"
            eng_body += f"  - Backend: {tech_stack.get('backend', 'N/A')}\n"
            eng_body += f"  - Database: {tech_stack.get('database', 'N/A')}\n"
            eng_body += f"  - Infrastructure: {tech_stack.get('infrastructure', 'N/A')}\n\n"
            
            if integrations:
                eng_body += f"-> REQUIRED INTEGRATIONS:\n"
                for i in integrations: eng_body += f"  - {i}\n"
                eng_body += "\n"
            
            eng_body += f"-> REQUIRED API ENDPOINTS:\n"
            for api in data.get("api_endpoints", []):
                eng_body += f"  - [{api.get('method')}] {api.get('route')}\n"
                
            eng_body += "\nPlease see the attached PDF for the full Database Schema breakdown, CI/CD pipeline, and Security requirements.\n\nBest,\nBridgeBuild Engineering Hub"
            eng_mailto = f"mailto:?subject={quote('Technical Architecture Specs')}&body={quote(eng_body)}"
            
            st.markdown(f"""
                <a href="{eng_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #333333; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 400; cursor: pointer; line-height: 1.6; font-size: 1rem; margin-top: 2px;">
                        Email Architecture Specs
                    </button>
                </a>
                """, unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Finalize Project")
        st.info("Architecture complete? Mark this project as fully scoped and ready for development.")

        if st.session_state.active_eng_ticket_id:
            if st.button("Mark as Ready for Dev", type="primary", use_container_width=True):
                try:
                    supabase.table("tickets").update({"status": "Ready for Dev", "target_department": "None"}).eq("id", st.session_state.active_eng_ticket_id).execute()
                    st.success("Architecture finalized and ready for the build!")
                except Exception as e:
                    st.error(f"Failed to finalize ticket: {str(e)}")

    # --- 3. ENGINEERING HISTORY SECTION ---
    st.divider()
    st.subheader("Saved Architecture Schemas")
    
    try:
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).eq("complexity", "Engineering Architecture").order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        if saved_tickets:
            for item in saved_tickets:
                
                current_status = item.get('status', 'Draft')
                if current_status in ['Draft', 'Accepted by Engineering']:
                    status_icon = "📝"
                else:
                    status_icon = "✅"

                with st.expander(f"{status_icon} Arch: {item['summary'][:60]}..."):
                    
                    if current_status in ['Draft', 'Accepted by Engineering']:
                        st.caption(f"Status: **{current_status} (Not Finalized)**")
                    else:
                        st.caption(f"Status: **{current_status}**")

                    past_data = json.loads(item['full_data'])
                    
                    hist_tech_stack = past_data.get("tech_stack_recommendation", {})
                    hist_body = f"Hello Dev Team,\n\nPlease review the generated System Architecture for a previous concept.\n\n"
                    hist_body += f"-> ARCHITECTURE OVERVIEW:\n{past_data.get('system_architecture', 'N/A')}\n\n"
                    hist_body += f"-> TECH STACK:\n"
                    hist_body += f"  - Frontend: {hist_tech_stack.get('frontend', 'N/A')}\n"
                    hist_body += f"  - Backend: {hist_tech_stack.get('backend', 'N/A')}\n"
                    hist_body += f"  - Database: {hist_tech_stack.get('database', 'N/A')}\n"
                    hist_body += f"  - Infrastructure: {hist_tech_stack.get('infrastructure', 'N/A')}\n\n"
                    
                    hist_ints = past_data.get("third_party_integrations", [])
                    if hist_ints:
                        hist_body += f"-> REQUIRED INTEGRATIONS:\n"
                        for i in hist_ints: hist_body += f"  - {i}\n"
                        hist_body += "\n"

                    hist_body += f"-> REQUIRED API ENDPOINTS:\n"
                    for api in past_data.get("api_endpoints", []): hist_body += f"  - [{api.get('method')}] {api.get('route')}\n"
                    hist_body += "\nSee the attached PDF for the full DB Schema.\n\nBest,\nBridgeBuild Engineering Hub"
                    hist_mailto = f"mailto:?subject={quote('Historical Technical Architecture Specs')}&body={quote(hist_body)}"

                    st.markdown(f"**Pipeline:** {past_data.get('ci_cd_pipeline', 'N/A')}")
                    
                    if hist_ints:
                        st.markdown("**Integrations:** " + ", ".join(hist_ints))
                        
                    hist_btn_col1, hist_btn_col2 = st.columns([3, 1])
                    with hist_btn_col1:
                        st.download_button("Download PDF", data=generate_local_eng_pdf(past_data), file_name=f"architecture_{item['id'][:8]}.pdf", mime="application/pdf", key=f"hist_pdf_eng_{item['id']}", use_container_width=True)
                        st.download_button("Download CSV (DB & API Schema)", data=generate_engineering_csv(past_data), file_name=f"engineering_schema_{item['id'][:8]}.csv", mime="text/csv", key=f"hist_csv_eng_{item['id']}", use_container_width=True)
                        
                    with hist_btn_col2:
                        with st.popover("Delete Schema", use_container_width=True):
                            st.warning("Are you sure? This cannot be undone.")
                            if st.button("Yes, Delete Forever", key=f"confirm_del_eng_{item['id']}", type="primary"):
                                try:
                                    supabase.table("tickets").delete().eq("id", item['id']).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete: {str(e)}")
                    
                    st.markdown(f"""
                        <div style="margin-top: 5px; margin-bottom: 15px;">
                            <a href="{hist_mailto}" target="_blank" style="text-decoration: none;">
                                <button style="width: 100%; background-color: #333333; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                    Email Architecture Specs
                                </button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    if current_status in ['Draft', 'Accepted by Engineering']:
                        st.markdown("##### Finalize Project")
                        if st.button("Mark as Ready for Dev", key=f"hist_ready_{item['id']}", use_container_width=True):
                            supabase.table("tickets").update({"status": "Ready for Dev", "target_department": "None"}).eq("id", item['id']).execute()
                            st.rerun()
                    
                    st.divider()
                    
                    col_hf1, col_hf2 = st.columns(2)
                    with col_hf1:
                        st.markdown("**Core Tables:**")
                        for table in past_data.get("database_schema", []):
                            st.caption(f"- `{table.get('table_name')}`")
                    with col_hf2:
                        st.markdown("**Key Routes:**")
                        for api in past_data.get("api_endpoints", [])[:3]: 
                            st.caption(f"- {api.get('method')} `{api.get('route')}`")
                            
        else:
            st.info("No saved architectures yet. Initialize a build above!")
            
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
