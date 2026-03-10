import streamlit as st
import json
import urllib.parse
import tempfile
import os
import io
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
    """Generates either the highly detailed Eng Ticket or the brief Sales summary."""
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
            
            # Only print Acceptance Criteria if it's the detailed report
            if is_detailed:
                for ac in item.get("acceptance_criteria", []):
                    y = _check_page_break(c, y, height)
                    c.drawString(50, y, "-")
                    y = _draw_wrapped_text(c, f"AC: {ac}", 60, y, 480, "Helvetica", 10)
            y -= 10
    
    if is_detailed:
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

    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# DASHBOARD RENDERER
# ==========================================
def render_pm_dashboard(supabase):
    with st.sidebar:
        st.markdown("#### 🏗️ Architecture Engine")
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

    if st.button("Load Sample Email", key="pm_load_sample_btn"):
        st.session_state.sales_input = "Client wants a mobile app for food delivery. Needs GPS tracking for drivers, a menu for customers, and a payment gateway. They have a budget of $15k."
    
    if "sales_input" not in st.session_state: 
        st.session_state.sales_input = ""

    uploaded_file = st.file_uploader("Upload Meeting Audio or Transcript (.mp3, .wav, .txt, .pdf)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']: st.audio(uploaded_file)
            
    sales_input = st.text_area("Paste Text or Add Extra Context:", value=st.session_state.sales_input, height=150)

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
                    
        with st.expander("Technical Risks", expanded=False):
            for risk in data.get("technical_risks", []): st.warning(f"- {risk}")

        # --- RESTORED DUAL EXPORT UI ---
        st.divider()
        col_action1, col_action2 = st.columns([1, 1], gap="medium")
        
        with col_action1:
            st.markdown("#### 📄 Export PDF Reports")
            st.download_button(
                "Download Detailed Ticket (Engineering)", 
                data=generate_local_pm_pdf(data, currency, is_detailed=True), 
                file_name="bridgebuild_detailed_ticket.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
            st.download_button(
                "Download Brief Summary (Sales / Client)", 
                data=generate_local_pm_pdf(data, currency, is_detailed=False), 
                file_name="bridgebuild_brief_summary.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
        
        with col_action2:
            st.markdown("#### ✉️ Share with Stakeholders")
            ticket_name = data.get('ticket_name', data.get('summary', 'New Project'))[:50]
            
            eng_body = f"Hello Engineering Team,\n\nPlease review the scoped Agile requirements...\n\n-> SUMMARY:\n{data.get('summary', 'N/A')}\n\nBest,\nProduct Management"
            eng_mailto = f"mailto:?subject={urllib.parse.quote(f'Eng Ticket: {ticket_name}')}&body={urllib.parse.quote(eng_body)}"
            
            sales_body = f"Hello Sales Team,\n\nGreat news—we have completed the initial feasibility scoping...\n\nBest,\nProduct Management"
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

    # --- HISTORY SECTION REMOVED FOR BREVITY (Keep your existing history block here) ---
