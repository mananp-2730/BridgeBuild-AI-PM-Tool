import streamlit as st
import json
import urllib.parse
import tempfile
import os
import io
import csv
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types
from prompts import get_system_prompt
from utils import clean_json_output, generate_jira_format, convert_currency, safe_parse_json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ==========================================
# LOCALIZED PM PDF ENGINES
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
    c.setFillColorRGB(0.004, 0.129, 0.412) 
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

def generate_local_pm_pdf(ticket_data, currency="USD ($)", is_detailed=True):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    report_title = "Engineering Ticket Report" if is_detailed else "Executive Scoping Summary"
    _draw_header(c, width, height, report_title)
    
    y = height - 140
    c.setFillColor(colors.black)

    name = ticket_data.get("ticket_name", ticket_data.get("summary", "Untitled"))
    y = _draw_wrapped_text(c, f"Project: {name}", 40, y, 500, "Helvetica-Bold", 16)
    y -= 15
    y = _draw_wrapped_text(c, ticket_data.get("summary", "No summary provided."), 40, y, 520, "Helvetica", 11)
    y -= 20

    raw_budget = ticket_data.get('budget_estimate_usd', '0')
    low = convert_currency(raw_budget.split("-")[0].strip() if "-" in raw_budget else raw_budget, currency)
    high = convert_currency(raw_budget.split("-")[1].strip() if "-" in raw_budget else raw_budget, currency)
    p1_budget = f"{low} - {high}"

    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.004, 0.129, 0.412)
    c.drawString(40, y, _safe_text("Phase 1: Core MVP"))
    y -= 20
    c.setFillColor(colors.black)
    c.drawString(40, y, _safe_text(f"Est. Time: {ticket_data.get('development_time', 'N/A')} | Est. Budget: {p1_budget}"))
    y -= 20
    
    if "mvp_user_stories" in ticket_data:
        for item in ticket_data.get("mvp_user_stories", []):
            y = _check_page_break(c, y, height)
            y = _draw_wrapped_text(c, f"Story: {item.get('story', '')}", 40, y, 500, "Helvetica-Bold", 10)
            
            if is_detailed:
                for ac in item.get("acceptance_criteria", []):
                    y = _check_page_break(c, y, height)
                    c.drawString(50, y, "-")
                    y = _draw_wrapped_text(c, f"AC: {ac}", 60, y, 480, "Helvetica", 10)
            y -= 10
    else:
        for feat in ticket_data.get("mvp_features", []):
            y = _check_page_break(c, y, height)
            c.drawString(45, y, "-")
            y = _draw_wrapped_text(c, feat, 60, y, 480, "Helvetica", 11)
            y -= 5

    if is_detailed:
        y -= 10
        y = _check_page_break(c, y, height)
        p2_raw = ticket_data.get("phase_2_budget_usd", "0-0")
        p2_low = convert_currency(p2_raw.split("-")[0] if "-" in p2_raw else p2_raw, currency)
        p2_high = convert_currency(p2_raw.split("-")[1] if "-" in p2_raw else p2_raw, currency)
        c.setFillColorRGB(0.004, 0.129, 0.412)
        c.drawString(40, y, _safe_text("Phase 2: Future Enhancements"))
        y -= 20
        c.setFillColor(colors.black)
        c.drawString(40, y, _safe_text(f"Est. Extra Time: {ticket_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_low} - {p2_high}"))
        y -= 20
        
        for feat in ticket_data.get("phase_2_features", []):
            y = _check_page_break(c, y, height)
            c.drawString(45, y, "-")
            y = _draw_wrapped_text(c, feat, 60, y, 480, "Helvetica", 11)
            y -= 5

        y -= 10
        y = _check_page_break(c, y, height)
        c.setFillColorRGB(0.004, 0.129, 0.412)
        c.drawString(40, y, _safe_text("Technical Risks"))
        y -= 20
        c.setFillColor(colors.black)
        for risk in ticket_data.get("technical_risks", []):
            y = _check_page_break(c, y, height)
            c.drawString(45, y, "-")
            y = _draw_wrapped_text(c, risk, 60, y, 490, "Helvetica", 11)
            y -= 5

        y -= 10
        y = _check_page_break(c, y, height)
        c.setFillColorRGB(0.004, 0.129, 0.412)
        c.drawString(40, y, _safe_text("Suggested Tech Stack"))
        y -= 20
        c.setFillColor(colors.black)
        for item in ticket_data.get("suggested_stack", []):
            y = _check_page_break(c, y, height)
            c.drawString(45, y, "-")
            y = _draw_wrapped_text(c, item, 60, y, 490, "Helvetica", 11)
            y -= 5

    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# JIRA/LINEAR CSV EXPORTER ENGINE
# ==========================================
def generate_jira_csv(ticket_data):
    """Converts the JSON ticket data into a bulk-import friendly CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Standard Jira Import Headers
    writer.writerow(["Issue Type", "Summary", "Description", "Priority"])
    
    project_summary = ticket_data.get("summary", "No project summary provided.")
    
    if "mvp_user_stories" in ticket_data:
        for item in ticket_data.get("mvp_user_stories", []):
            story_title = item.get("story", "User Story")
            ac_list = item.get("acceptance_criteria", [])
            
            # Format the description beautifully for Jira
            description = f"Context:\n{project_summary}\n\nAcceptance Criteria:\n"
            for ac in ac_list:
                description += f"- {ac}\n"
                
            writer.writerow(["Story", story_title, description, "Highest"])
    else:
        for feat in ticket_data.get("mvp_features", []):
            writer.writerow(["Story", feat, f"Context:\n{project_summary}", "Highest"])
            
    # Optionally export Phase 2 as Low Priority
    for feat in ticket_data.get("phase_2_features", []):
        writer.writerow(["Story", f"[Phase 2] {feat}", "Future enhancement", "Low"])
        
    return output.getvalue().encode('utf-8')

# ==========================================
# PM DASHBOARD RENDERER
# ==========================================
def render_pm_dashboard(supabase):
    
    with st.sidebar:
        st.markdown("#### Architecture Engine")
        build_strategy = st.select_slider(
            "Build Strategy:", 
            options=["Speed (Low-Code/MVP)", "Balanced", "Scale (Enterprise/Microservices)"], 
            value="Balanced"
        )

    user_prefs = st.session_state.get("user_prefs", {})
    currency = user_prefs.get("currency", "USD ($)")
    rate_type = user_prefs.get("rate_standard", "US Agency ($150/hr)")
    model_choice = user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")
    api_key = st.secrets.get("GOOGLE_API_KEY")

    st.title("BridgeBuild AI - PM Hub")
    st.markdown("### Translate vague sales requests into structured Agile tickets.")

    if "sales_input" not in st.session_state: 
        st.session_state.sales_input = ""

    # ==========================================
    # INCOMING SALES QUEUE (INBOX)
    # ==========================================
    try:
        inbox_res = supabase.table("tickets").select("*").eq("status", "Awaiting PM Scoping").eq("target_department", "PM").order("created_at", desc=True).execute()
        inbox_tickets = inbox_res.data
        
        if inbox_tickets:
            st.info(f"📥 **INCOMING:** You have {len(inbox_tickets)} approved project(s) from Sales waiting in your queue!")
            for item in inbox_tickets:
                with st.expander(f"🟢 Approved Sales Deal: {item['summary'][:60]}..."):
                    try:
                        sales_data = json.loads(item['full_data'])
                    except:
                        sales_data = {}
                        
                    st.write(f"**Approved Budget:** {item['cost']} | **Timeline:** {item['time']}")
                    st.caption("**Deal Breakers to watch out for:**")
                    for db in sales_data.get("deal_breakers", []):
                        st.error(f"- {db}")
                        
                    if st.button("Accept & Load into Generator", key=f"accept_{item['id']}", type="primary"):
                        supabase.table("tickets").update({"status": "Accepted by PM"}).eq("id", item['id']).execute()
                        
                        injection_text = f"SALES HANDOFF CONTEXT:\nProject Summary: {sales_data.get('project_summary', item['summary'])}\nBudget: {item['cost']}\nTimeline: {item['time']}\nDeal Breakers: {sales_data.get('deal_breakers', [])}\nClient Asks: {sales_data.get('client_questions', [])}"
                        st.session_state.sales_input = injection_text
                        st.rerun()
            st.divider()
    except Exception as e:
        st.warning(f"Could not load Inbox: {str(e)}")

    # ==========================================
    # GENERATOR UI
    # ==========================================
    if st.button("Load Sample Email", key="pm_load_sample_btn"):
        st.session_state.sales_input = "Client wants a mobile app for food delivery. Needs GPS tracking for drivers, a menu for customers, and a payment gateway. They have a budget of $15k."
    
    uploaded_file = st.file_uploader("Upload Meeting Audio or Transcript (.mp3, .wav, .txt, .pdf)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']: st.audio(uploaded_file)
            
    sales_input = st.text_area("Paste Text or Review Sales Context:", value=st.session_state.sales_input, height=150)

    if "active_ticket" not in st.session_state: st.session_state.active_ticket = None
    if "active_ticket_id" not in st.session_state: st.session_state.active_ticket_id = None

    if st.button("Generate Ticket & Budget", type="primary"):
        if not api_key: st.error("System Error: AI Engine is currently offline.")
        elif not sales_input and not uploaded_file: st.warning("Please enter text or upload a file.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                SYSTEM_PROMPT = get_system_prompt(rate_type, build_strategy)
                
                with st.status("Consulting Engineering & Finance Teams...", expanded=True) as status:
                    st.write("Parsing input and extracting requirements...")
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.write("Processing multi-modal file...")
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
                        client.files.delete(name=gemini_file.name)
                    
                    st.write("Structuring Epics, Stories, and Budgets...")
                    data, error_msg = safe_parse_json(response.text)
                    
                    if error_msg:
                        status.update(label="Analysis Failed", state="error", expanded=True)
                        st.error(error_msg)
                        st.stop()
                    else:
                        status.update(label="Agile Ticket Generated!", state="complete", expanded=False)
                        
                st.session_state.active_ticket = data
                st.success("Analysis Complete!")

                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)

                # NEW PM TICKET SAVED TO DB
                new_ticket = {
                    "user_id": st.session_state.user.id, "summary": data.get("summary"), "cost": f"{fmt_low} - {fmt_high}",
                    "raw_cost": raw_cost, "complexity": data.get("complexity_score"), "time": data.get("development_time"), 
                    "full_data": json.dumps(data), "status": "Draft", "target_department": "None"
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
            st.markdown("#### Export Reports")
            st.download_button("Download Detailed Ticket (Engineering PDF)", data=generate_local_pm_pdf(data, currency, is_detailed=True), file_name="bridgebuild_detailed_ticket.pdf", mime="application/pdf", use_container_width=True)
            st.download_button("Download Brief Summary (Sales PDF)", data=generate_local_pm_pdf(data, currency, is_detailed=False), file_name="bridgebuild_brief_summary.pdf", mime="application/pdf", use_container_width=True)
            
            # --- NEW: CSV EXPORT BUTTON ---
            st.download_button("Download CSV (Jira/Linear Bulk Import)", data=generate_jira_csv(data), file_name="jira_bulk_import.csv", mime="text/csv", use_container_width=True)
        
        with col_action2:
            st.markdown("#### Share with Stakeholders")
            ticket_name = data.get('ticket_name', data.get('summary', 'New Project'))[:50]
            
            p2_raw_email = data.get("phase_2_budget_usd", "0-0")
            p2_low_email = convert_currency(p2_raw_email.split("-")[0].strip() if "-" in p2_raw_email else p2_raw_email, currency)
            p2_high_email = convert_currency(p2_raw_email.split("-")[1].strip() if "-" in p2_raw_email else p2_raw_email, currency)

            eng_body = f"Hello Engineering Team,\n\nPlease review the scoped Agile requirements for: {ticket_name}\n\n"
            eng_body += f"-> SUMMARY:\n{data.get('summary', 'N/A')}\n\n"
            eng_body += f"-> PHASE 1: CORE MVP\nEst. Time: {data.get('development_time', 'N/A')} | Est. Budget: {fmt_low} - {fmt_high}\n"
            if "mvp_user_stories" in data:
                for item in data.get("mvp_user_stories", []):
                    eng_body += f"\nStory: {item.get('story')}\n"
                    for ac in item.get("acceptance_criteria", []): eng_body += f"  - AC: {ac}\n"
            else:
                for feat in data.get("mvp_features", []): eng_body += f"  - {feat}\n"
            eng_body += f"\n\n-> PHASE 2: FUTURE ENHANCEMENTS\nEst. Extra Time: {data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_low_email} - {p2_high_email}\n"
            for feat in data.get("phase_2_features", []): eng_body += f"  - {feat}\n"
            eng_body += f"\n\n-> TECHNICAL RISKS\n"
            for risk in data.get("technical_risks", []): eng_body += f"  - {risk}\n"
            eng_body += f"\n\n-> SUGGESTED TECH STACK\n"
            for tech in data.get("suggested_stack", []): eng_body += f"  - {tech}\n"
            eng_body += "\n\nBest,\nProduct Management"
            eng_mailto = f"mailto:?subject={urllib.parse.quote(f'Eng Ticket: {ticket_name}')}&body={urllib.parse.quote(eng_body)}"
            
            sales_body = f"Hello Sales Team,\n\nHere is the initial feasibility scoping for {ticket_name}:\n\n"
            sales_body += f"-> SUMMARY:\n{data.get('summary', 'N/A')}\n\n"
            sales_body += f"-> PHASE 1: CORE MVP\nEst. Time: {data.get('development_time', 'N/A')} | Est. Budget: {fmt_low} - {fmt_high}\n"
            if "mvp_user_stories" in data:
                for item in data.get("mvp_user_stories", []): sales_body += f"  - {item.get('story')}\n"
            else:
                for feat in data.get("mvp_features", []): sales_body += f"  - {feat}\n"
            sales_body += f"\n\n-> PHASE 2: FUTURE ENHANCEMENTS\nEst. Extra Time: {data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_low_email} - {p2_high_email}\n"
            for feat in data.get("phase_2_features", []): sales_body += f"  - {feat}\n"
            sales_body += "\n\nSee the attached PDF for the client-facing Executive Summary.\n\nBest,\nProduct Management"
            sales_mailto = f"mailto:?subject={urllib.parse.quote(f'Sales Scoping: {ticket_name}')}&body={urllib.parse.quote(sales_body)}"
            
            st.markdown(f"""
                <a href="{eng_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-bottom: 10px;">
                        Email to Engineering
                    </button>
                </a>
                <a href="{sales_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #2E7D32; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                        Email to Sales
                    </button>
                </a>
                """, unsafe_allow_html=True)
            
        with st.expander("View Jira / Confluence Markup", expanded=False):
            st.code(generate_jira_format(data, currency), language="jira")

        # ==========================================
        # THE ACTIVE TICKET HANDOFF PROTOCOL
        # ==========================================
        st.divider()
        st.markdown("#### Department Handoff")
        st.info("Agile Scope Approved? Route this ticket to the next phase of development.")

        if st.session_state.active_ticket_id:
            col_handoff1, col_handoff2 = st.columns(2)
            with col_handoff1:
                if st.button("Approve & Send to Design", type="primary", use_container_width=True):
                    try:
                        supabase.table("tickets").update({"status": "Awaiting UI/UX Scoping", "target_department": "Design"}).eq("id", st.session_state.active_ticket_id).execute()
                        st.success("Boom! Successfully routed to the Design Inbox.")
                    except Exception as e:
                        st.error(f"Failed to handoff ticket: {str(e)}")
            with col_handoff2:
                if st.button("Approve & Send to Engineering", type="primary", use_container_width=True):
                    try:
                        supabase.table("tickets").update({"status": "Awaiting Tech Architecture", "target_department": "Engineering"}).eq("id", st.session_state.active_ticket_id).execute()
                        st.success("Boom! Successfully routed to the Engineering Inbox.")
                    except Exception as e:
                        st.error(f"Failed to handoff ticket: {str(e)}")
                
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
                            supabase.table("tickets").update({"summary": updated_data.get("summary"), "complexity": updated_data.get("complexity_score"), "time": updated_data.get("development_time"), "full_data": json.dumps(updated_data)}).eq("id", st.session_state.active_ticket_id).execute()
                            
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Failed to refine: {str(e)}")

    st.divider()
    st.subheader("Saved Tickets History")
    try:
        # Changed to only show PM tickets in the PM history!
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).neq("complexity", "Engineering Architecture").neq("complexity", "UI/UX Scoping").order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        # Filter out Sales tickets from the PM History view
        pm_tickets = [t for t in saved_tickets if t.get('complexity') not in ['Green', 'Yellow', 'Red']]
        
        if pm_tickets:
            for i, item in enumerate(pm_tickets):
                
                # --- NEW: STATUS BADGE LOGIC ---
                current_status = item.get('status', 'Draft')
                if current_status in ['Draft', 'Accepted by PM']:
                    status_icon = "📝"
                elif current_status == 'Awaiting UI/UX Scoping':
                    status_icon = "🎨"
                elif current_status == 'Awaiting Tech Architecture':
                    status_icon = "⚙️"
                else:
                    status_icon = "✅"
                
                with st.expander(f"{status_icon} Ticket: {item['summary'][:60]}..."):
                    try:
                        past_data = json.loads(clean_json_output(item['full_data']))
                    except:
                        past_data = {}
                        
                    # --- SHOW CURRENT STATUS ---
                    if current_status in ['Draft', 'Accepted by PM']:
                        st.caption(f"Status: **{current_status} (Not Sent)**")
                    else:
                        st.caption(f"Status: **{current_status}** 🚀")

                    hist_raw_cost = past_data.get("budget_estimate_usd", "0-0")
                    hist_low = convert_currency(hist_raw_cost.split("-")[0].strip() if "-" in hist_raw_cost else hist_raw_cost, currency)
                    hist_high = convert_currency(hist_raw_cost.split("-")[1].strip() if "-" in hist_raw_cost else hist_raw_cost, currency)
                    p2_raw_email = past_data.get("phase_2_budget_usd", "0-0")
                    p2_low_email = convert_currency(p2_raw_email.split("-")[0].strip() if "-" in p2_raw_email else p2_raw_email, currency)
                    p2_high_email = convert_currency(p2_raw_email.split("-")[1].strip() if "-" in p2_raw_email else p2_raw_email, currency)
                    
                    ticket_name = past_data.get('ticket_name', past_data.get('summary', 'New Project'))[:50]
                    
                    eng_body = f"Hello Engineering Team,\n\nPlease review the scoped Agile requirements for: {ticket_name}\n\n"
                    eng_body += f"-> SUMMARY:\n{past_data.get('summary', 'N/A')}\n\n"
                    eng_body += f"-> PHASE 1: CORE MVP\nEst. Time: {past_data.get('development_time', 'N/A')} | Est. Budget: {hist_low} - {hist_high}\n"
                    if "mvp_user_stories" in past_data:
                        for story in past_data.get("mvp_user_stories", []):
                            eng_body += f"\nStory: {story.get('story')}\n"
                            for ac in story.get("acceptance_criteria", []): eng_body += f"  - AC: {ac}\n"
                    else:
                        for feat in past_data.get("mvp_features", []): eng_body += f"  - {feat}\n"
                    eng_body += f"\n\n-> PHASE 2: FUTURE ENHANCEMENTS\nEst. Extra Time: {past_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_low_email} - {p2_high_email}\n"
                    for feat in past_data.get("phase_2_features", []): eng_body += f"  - {feat}\n"
                    eng_body += f"\n\n-> TECHNICAL RISKS\n"
                    for risk in past_data.get("technical_risks", []): eng_body += f"  - {risk}\n"
                    eng_body += f"\n\n-> SUGGESTED TECH STACK\n"
                    for tech in past_data.get("suggested_stack", []): eng_body += f"  - {tech}\n"
                    eng_body += "\n\nBest,\nProduct Management"
                    eng_mailto = f"mailto:?subject={urllib.parse.quote(f'Eng Ticket: {ticket_name}')}&body={urllib.parse.quote(eng_body)}"

                    sales_body = f"Hello Sales Team,\n\nHere is the initial feasibility scoping for {ticket_name}:\n\n"
                    sales_body += f"-> SUMMARY:\n{past_data.get('summary', 'N/A')}\n\n"
                    sales_body += f"-> PHASE 1: CORE MVP\nEst. Time: {past_data.get('development_time', 'N/A')} | Est. Budget: {hist_low} - {hist_high}\n"
                    if "mvp_user_stories" in past_data:
                        for story in past_data.get("mvp_user_stories", []): sales_body += f"  - {story.get('story')}\n"
                    else:
                        for feat in past_data.get("mvp_features", []): sales_body += f"  - {feat}\n"
                    sales_body += f"\n\n-> PHASE 2: FUTURE ENHANCEMENTS\nEst. Extra Time: {past_data.get('phase_2_time', 'N/A')} | Est. Extra Budget: {p2_low_email} - {p2_high_email}\n"
                    for feat in past_data.get("phase_2_features", []): sales_body += f"  - {feat}\n"
                    sales_body += "\n\nSee the attached PDF for the client-facing Executive Summary.\n\nBest,\nProduct Management"
                    sales_mailto = f"mailto:?subject={urllib.parse.quote(f'Sales Scoping: {ticket_name}')}&body={urllib.parse.quote(sales_body)}"

                    hist_btn_col1, hist_btn_col3 = st.columns([4, 1])
                    with hist_btn_col1:
                        st.download_button("Download PDF", data=generate_local_pm_pdf(past_data, currency, is_detailed=True), file_name=f"ticket_{item['id'][:8]}.pdf", mime="application/pdf", key=f"hist_pdf_{item['id']}", use_container_width=True)
                        
                        # --- NEW: HISTORY CSV EXPORT BUTTON ---
                        st.download_button("Download CSV", data=generate_jira_csv(past_data), file_name=f"jira_import_{item['id'][:8]}.csv", mime="text/csv", key=f"hist_csv_{item['id']}", use_container_width=True)
                        
                    with hist_btn_col3:
                        if st.button("Delete", key=f"del_{item['id']}", use_container_width=True):
                            try:
                                supabase.table("tickets").delete().eq("id", item['id']).execute()
                                st.rerun() 
                            except Exception as e:
                                st.error(f"Failed to delete ticket: {str(e)}")
                    
                    st.markdown(f"""
                        <div style="display: flex; gap: 10px; margin-top: 10px; margin-bottom: 10px;">
                            <a href="{eng_mailto}" target="_blank" style="text-decoration: none; flex: 1;">
                                <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                    Email Eng
                                </button>
                            </a>
                            <a href="{sales_mailto}" target="_blank" style="text-decoration: none; flex: 1;">
                                <button style="width: 100%; background-color: #2E7D32; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                    Email Sales
                                </button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # --- HISTORY HANDOFF BUTTONS ---
                    if current_status in ['Draft', 'Accepted by PM']:
                        st.markdown("##### Route Ticket")
                        hist_hand_col1, hist_hand_col2 = st.columns(2)
                        with hist_hand_col1:
                            if st.button("Send to Design", key=f"hist_design_{item['id']}", use_container_width=True):
                                supabase.table("tickets").update({"status": "Awaiting UI/UX Scoping", "target_department": "Design"}).eq("id", item['id']).execute()
                                st.rerun()
                        with hist_hand_col2:
                            if st.button("Send to Engineering", key=f"hist_eng_{item['id']}", use_container_width=True):
                                supabase.table("tickets").update({"status": "Awaiting Tech Architecture", "target_department": "Engineering"}).eq("id", item['id']).execute()
                                st.rerun()

                    with st.expander("🎫 View Jira / Confluence Markup", expanded=False):
                        st.code(generate_jira_format(past_data, currency), language="jira")
        else:
            st.info("No saved PM tickets yet. Generate your first one above!")
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
