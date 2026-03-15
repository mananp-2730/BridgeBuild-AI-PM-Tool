import streamlit as st
import json
import os
import tempfile
import io
import re
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types
from prompts import get_design_prompt
from utils import safe_parse_json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ==========================================
# LOCALIZED DESIGN PDF ENGINE
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
    c.setFillColorRGB(0.5, 0.1, 0.5) # Purple header for Design Studio
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

def generate_local_design_pdf(ticket_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    _draw_header(c, width, height, "UX/UI Design Architecture")
    y = height - 140
    c.setFillColor(colors.black)
    
    y = _draw_wrapped_text(c, "Project Vision:", 40, y, 500, "Helvetica-Bold", 14)
    y -= 5
    y = _draw_wrapped_text(c, ticket_data.get('project_vision', 'N/A'), 40, y, 500, "Helvetica", 11)
    y -= 15

    theme = ticket_data.get("design_theme", {})
    y = _draw_wrapped_text(c, f"Target Audience: {ticket_data.get('target_audience', 'N/A')}", 40, y, 500, "Helvetica-Bold", 11)
    y = _draw_wrapped_text(c, f"The Vibe: {theme.get('vibe', 'N/A')}", 40, y, 500, "Helvetica-Bold", 11)
    y = _draw_wrapped_text(c, f"Typography: {theme.get('typography_pairing', 'N/A')}", 40, y, 500, "Helvetica-Bold", 11)
    y = _draw_wrapped_text(c, f"Primary Color Hex: {theme.get('primary_color_suggestion', 'N/A')}", 40, y, 500, "Helvetica-Bold", 11)
    y -= 20

    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.5, 0.1, 0.5)
    c.drawString(40, y, _safe_text("Core User Flows"))
    y -= 20
    c.setFillColor(colors.black)
    
    for flow in ticket_data.get("core_user_flows", []):
        y = _check_page_break(c, y, height)
        y = _draw_wrapped_text(c, f"Flow: {flow.get('flow_name', 'Unnamed')}", 40, y, 480, "Helvetica-Bold", 11)
        for step in flow.get("steps", []):
            y = _check_page_break(c, y, height)
            c.drawString(50, y, "-")
            y = _draw_wrapped_text(c, step, 60, y, 460, "Helvetica", 10)
        y -= 5

    y -= 10
    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.5, 0.1, 0.5)
    c.drawString(40, y, _safe_text("Key Screens & Core Elements"))
    y -= 20
    c.setFillColor(colors.black)
    
    for screen in ticket_data.get("key_screens", []):
        y = _check_page_break(c, y, height)
        y = _draw_wrapped_text(c, f"Screen: {screen.get('screen_name', 'Unnamed')}", 40, y, 480, "Helvetica-Bold", 11)
        for elem in screen.get("core_elements", []):
            y = _check_page_break(c, y, height)
            c.drawString(50, y, "🔹")
            y = _draw_wrapped_text(c, elem, 65, y, 460, "Helvetica", 10)
        y -= 5

    y -= 10
    y = _check_page_break(c, y, height)
    c.setFillColorRGB(0.5, 0.1, 0.5)
    c.drawString(40, y, _safe_text("Accessibility (a11y) Requirements"))
    y -= 20
    c.setFillColor(colors.black)
    for a11y in ticket_data.get("accessibility_a11y", []):
        y = _check_page_break(c, y, height)
        c.drawString(45, y, "✓")
        y = _draw_wrapped_text(c, a11y, 60, y, 480, "Helvetica", 11)

    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# DESIGN DASHBOARD RENDERER
# ==========================================
def render_design_dashboard(supabase):

    st.title("BridgeBuild AI - UX/UI Design Intake")
    st.markdown("### Transform messy client ideas into structured user flows and screen layouts.")

    if "design_input" not in st.session_state: 
        st.session_state.design_input = ""
        
    # Initialize State Management
    if "active_design_ticket" not in st.session_state: 
        st.session_state.active_design_ticket = None
    if "active_design_ticket_id" not in st.session_state: 
        st.session_state.active_design_ticket_id = None

    # ==========================================
    # NEW: INCOMING PM QUEUE (INBOX)
    # ==========================================
    try:
        inbox_res = supabase.table("tickets").select("*").eq("status", "Awaiting UI/UX Scoping").eq("target_department", "Design").order("created_at", desc=True).execute()
        inbox_tickets = inbox_res.data
        
        if inbox_tickets:
            st.info(f"**INCOMING:** You have {len(inbox_tickets)} approved Agile ticket(s) from the PM Hub waiting for Design!")
            for item in inbox_tickets:
                with st.expander(f"Incoming Agile Ticket: {item['summary'][:60]}..."):
                    try:
                        pm_data = json.loads(item['full_data'])
                    except:
                        pm_data = {}
                        
                    st.write(f"**Dev Time:** {item['time']} | **Complexity:** {item['complexity']}")
                    
                    if st.button("Accept & Load into Studio", key=f"accept_{item['id']}", type="primary"):
                        # 1. Update the original PM ticket so it leaves the queue
                        supabase.table("tickets").update({"status": "Accepted by Design"}).eq("id", item['id']).execute()
                        
                        # 2. Inject the highly structured PM data into the Designer's text area!
                        injection_text = f"PM HANDOFF CONTEXT:\nProject Summary: {pm_data.get('summary', item['summary'])}\n"
                        if "mvp_user_stories" in pm_data:
                            injection_text += "User Stories to Design For:\n"
                            for story in pm_data.get("mvp_user_stories", []):
                                injection_text += f"- {story.get('story')}\n"
                        else:
                            injection_text += f"Features to Design For: {pm_data.get('mvp_features', [])}\n"
                            
                        st.session_state.design_input = injection_text
                        st.rerun()
            st.divider()
    except Exception as e:
        st.warning(f"Could not load Inbox: {str(e)}")

    # ==========================================
    # GENERATOR UI
    # ==========================================
    uploaded_file = st.file_uploader("Upload Client Audio/Notes (.mp3, .wav)", type=["mp3", "wav", "m4a", "txt", "pdf"])
    
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']:
            st.audio(uploaded_file)
            
    design_input = st.text_area("Paste Text or Review PM Context:", value=st.session_state.design_input, height=150, placeholder="Example: Client wants a fitness app where users can track workouts and share with friends. Needs to feel modern and energetic.")

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

                with st.status("Initializing Design Studio...", expanded=True) as status:
                    st.write("Empathizing with target audience...")
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.write("Listening to client vibe and requirements...")
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)
                    
                    st.write("Sketching core user flows and wireframe layouts...")
                    text_instruction = design_input if design_input else "Extract UX/UI design requirements from this request."
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=DESIGN_PROMPT,
                            temperature=0.4,
                            response_mime_type="application/json"
                        ),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        st.write("Cleaning up workspace...")
                        client.files.delete(name=gemini_file.name)
                    
                    st.write("Selecting color palettes and accessibility standards...")
                    data, error_msg = safe_parse_json(response.text)
                    
                    if error_msg:
                        status.update(label="Architecture Failed", state="error", expanded=True)
                        st.error(error_msg)
                        st.stop()
                    else:
                        status.update(label="Design Architecture Complete!", state="complete", expanded=False)
                        st.session_state.active_design_ticket = data

                # SAVE TO SUPABASE WITH STATUS
                new_ticket = {
                    "user_id": st.session_state.user.id,
                    "summary": data.get("project_vision", "Design Architecture")[:200],
                    "cost": "N/A (Design Phase)",
                    "raw_cost": "0-0",
                    "complexity": "UI/UX Scoping", 
                    "time": "TBD",
                    "full_data": response.text,
                    "status": "Draft",
                    "target_department": "None"
                }
                db_res = supabase.table("tickets").insert(new_ticket).execute()
                st.session_state.active_design_ticket_id = db_res.data[0]['id']
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # ==========================================
    # RENDER THE ACTIVE DESIGN UI (POLISHED)
    # ==========================================
    if st.session_state.active_design_ticket:
        data = st.session_state.active_design_ticket
        
        st.write("")
        st.success("Design Architecture Ready!")
        
        # --- HERO SECTION ---
        with st.container(border=True):
            st.markdown("#### Project Vision")
            st.info(data.get('project_vision'))
            st.markdown(f"**Target Audience:** {data.get('target_audience')}")
        
        st.write("")
        
        # --- THEME & COLOR SWATCH CARD ---
        theme = data.get("design_theme", {})
        vibe = theme.get("vibe", "Modern & Clean")
        typography = theme.get("typography_pairing", "Standard sans-serif")
        raw_color_text = theme.get("primary_color_suggestion", "#012169")
        match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', raw_color_text)
        safe_hex = match.group(0) if match else "#012169"

        with st.container(border=True):
            col_vibe, col_color = st.columns(2)
            with col_vibe:
                st.markdown("#### The Vibe")
                st.write(f"*{vibe}*")
                st.markdown("#### Typography")
                st.write(f"*{typography}*")
            with col_color:
                st.markdown("#### Primary Color")
                # Massive dynamic color swatch
                st.markdown(f"""
                <div style='background-color: {safe_hex}; color: white; padding: 15px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; letter-spacing: 2px; box-shadow: inset 0 0 10px rgba(0,0,0,0.2);'>
                    {raw_color_text}
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core User Flows")
            for flow in data.get("core_user_flows", []):
                with st.expander(f"Flow: {flow.get('flow_name', 'User Flow')}"):
                    for step in flow.get("steps", []):
                        st.markdown(f"- {step}")
                        
            st.write("")
            st.markdown("#### UI Component Library")
            # --- INLINE COMPONENT PILLS ---
            components_html = ""
            for comp in data.get("ui_components_needed", []):
                components_html += f"<span style='background-color: #e2e8f0; color: #1e293b; padding: 6px 12px; border-radius: 20px; margin-right: 8px; margin-bottom: 8px; display: inline-block; font-size: 13px; font-weight: 600; border: 1px solid #cbd5e1;'>{comp}</span>"
            st.markdown(components_html, unsafe_allow_html=True)

        with col2:
            st.markdown("#### Key Screens & Layouts")
            for screen in data.get("key_screens", []):
                with st.container(border=True):
                    st.markdown(f"**{screen.get('screen_name', 'Screen')}**")
                    for elem in screen.get("core_elements", []):
                        st.caption(f"🔹 {elem}")
                        
            st.write("")
            st.markdown("#### Accessibility (a11y)")
            for a11y in data.get("accessibility_a11y", []):
                st.success(f"✓ {a11y}")

        # --- EXPLICIT DESIGN EXPORT & EMAIL UI ---
        st.divider()
        col_action1, col_action2 = st.columns([1, 1], gap="medium")
        
        with col_action1:
            st.markdown("#### Export Design Specs")
            st.download_button(
                "Download Design PDF", 
                data=generate_local_design_pdf(data), 
                file_name="bridgebuild_design_specs.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
            
        with col_action2:
            st.markdown("#### Share with Design Team")
            
            design_body = f"Hello Design Team,\n\nPlease review the UX/UI Architecture for our next project.\n\n"
            design_body += f"-> PROJECT VISION:\n{data.get('project_vision', 'N/A')}\n\n"
            design_body += f"-> TARGET AUDIENCE: {data.get('target_audience', 'N/A')}\n"
            design_body += f"-> THE VIBE: {vibe}\n"
            design_body += f"-> TYPOGRAPHY: {typography}\n"
            design_body += f"-> PRIMARY HEX: {raw_color_text}\n\n"
            
            design_body += f"-> KEY SCREENS TO DESIGN:\n"
            for screen in data.get("key_screens", []):
                design_body += f"  - {screen.get('screen_name')}\n"
                
            design_body += f"\n-> CORE USER FLOWS:\n"
            for flow in data.get("core_user_flows", []):
                design_body += f"  - {flow.get('flow_name')}\n"
                
            design_body += "\nPlease see the attached PDF for a full breakdown of the layout elements, component library, and a11y requirements.\n\nBest,\nBridgeBuild Design Hub"
            design_mailto = f"mailto:?subject={quote('UX/UI Design Architecture Specs')}&body={quote(design_body)}"
            
            st.markdown(f"""
                <a href="{design_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #6A1B9A; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 400; cursor: pointer; line-height: 1.6; font-size: 1rem; margin-top: 2px;">
                        Email Design Specs
                    </button>
                </a>
                """, unsafe_allow_html=True)

        # ==========================================
        # THE ACTIVE TICKET HANDOFF PROTOCOL
        # ==========================================
        st.divider()
        st.markdown("#### Department Handoff")
        st.info("Design complete? Route this visually scoped ticket to Engineering for Tech Architecture.")

        if st.session_state.get("active_design_ticket_id"):
            if st.button("Approve & Send to Engineering", type="primary", use_container_width=True):
                try:
                    supabase.table("tickets").update({"status": "Awaiting Tech Architecture", "target_department": "Engineering"}).eq("id", st.session_state.active_design_ticket_id).execute()
                    st.success("Successfully routed to the Engineering Inbox.")
                except Exception as e:
                    st.error(f"Failed to handoff ticket: {str(e)}")

    # --- 3. DESIGN HISTORY SECTION ---
    st.divider()
    st.subheader("Saved Design Architectures")
    
    try:
        db_response = supabase.table("tickets").select("*").eq("user_id", st.session_state.user.id).eq("complexity", "UI/UX Scoping").order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        if saved_tickets:
            for item in saved_tickets:
                
                # --- NEW: STATUS BADGE LOGIC ---
                current_status = item.get('status', 'Draft')
                if current_status in ['Draft', 'Accepted by Design']:
                    status_icon = "📝"
                elif current_status == 'Awaiting Tech Architecture':
                    status_icon = "⚙️"
                else:
                    status_icon = "✅"

                with st.expander(f"{status_icon} Design: {item['summary'][:60]}..."):
                    
                    # --- SHOW CURRENT STATUS ---
                    if current_status in ['Draft', 'Accepted by Design']:
                        st.caption(f"Status: **{current_status} (Not Sent)**")
                    else:
                        st.caption(f"Status: **{current_status}** 🚀")

                    past_data = json.loads(item['full_data'])
                    theme = past_data.get("design_theme", {})
                    
                    # History Email Payload
                    hist_vibe = theme.get("vibe", "Modern & Clean")
                    hist_typography = theme.get("typography_pairing", "Standard sans-serif")
                    hist_hex = theme.get("primary_color_suggestion", "#012169")
                    hist_body = f"Hello Design Team,\n\nPlease review the UX/UI Architecture for a past project concept.\n\n"
                    hist_body += f"-> PROJECT VISION:\n{past_data.get('project_vision', 'N/A')}\n\n"
                    hist_body += f"-> THE VIBE: {hist_vibe}\n"
                    hist_body += f"-> TYPOGRAPHY: {hist_typography}\n"
                    hist_body += f"-> PRIMARY HEX: {hist_hex}\n\n"
                    hist_body += f"-> KEY SCREENS TO DESIGN:\n"
                    for screen in past_data.get("key_screens", []): hist_body += f"  - {screen.get('screen_name')}\n"
                    hist_body += "\nSee the attached PDF for full specs.\n\nBest,\nBridgeBuild Design Hub"
                    hist_mailto = f"mailto:?subject={quote('Historical UX/UI Design Specs')}&body={quote(hist_body)}"

                    # Add the color swatch to history too!
                    match_hist = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', hist_hex)
                    safe_hist_hex = match_hist.group(0) if match_hist else "#012169"
                    st.markdown(f"**Vibe:** {hist_vibe} | **Font:** {hist_typography} | **Color:** <span style='background-color: {safe_hist_hex}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;'>{hist_hex}</span>", unsafe_allow_html=True)
                    
                    # Render localized PDF and Delete inside History
                    hist_btn_col1, hist_btn_col2 = st.columns([3, 1])
                    with hist_btn_col1:
                        st.download_button("Download PDF", data=generate_local_design_pdf(past_data), file_name=f"design_{item['id'][:8]}.pdf", mime="application/pdf", key=f"hist_pdf_design_{item['id']}", use_container_width=True)
                    with hist_btn_col2:
                        with st.popover("Delete", use_container_width=True):
                            st.warning("Are you sure?")
                            if st.button("Confirm Delete", key=f"confirm_del_design_{item['id']}", type="primary"):
                                try:
                                    supabase.table("tickets").delete().eq("id", item['id']).execute()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete: {str(e)}")
                    
                    # Embed Email Button
                    st.markdown(f"""
                        <div style="margin-top: 5px; margin-bottom: 15px;">
                            <a href="{hist_mailto}" target="_blank" style="text-decoration: none;">
                                <button style="width: 100%; background-color: #6A1B9A; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                    Email Design Specs
                                </button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # --- NEW: HISTORY HANDOFF BUTTONS ---
                    if current_status in ['Draft', 'Accepted by Design']:
                        st.markdown("##### Route Ticket")
                        if st.button("Send to Engineering", key=f"hist_eng_{item['id']}", use_container_width=True):
                            supabase.table("tickets").update({"status": "Awaiting Tech Architecture", "target_department": "Engineering"}).eq("id", item['id']).execute()
                            st.rerun()

                    st.divider()
                    
                    col_hf1, col_hf2 = st.columns(2)
                    with col_hf1:
                        st.markdown("**Core Screens:**")
                        for screen in past_data.get("key_screens", []):
                            st.caption(f"- {screen.get('screen_name')}")
                    with col_hf2:
                        st.markdown("**Key UI Components:**")
                        for comp in past_data.get("ui_components_needed", [])[:4]: 
                            st.caption(f"- {comp}")
                            
        else:
            st.info("No saved design concepts yet. Start ideating above!")
            
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
