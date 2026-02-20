"""
BridgeBuild AI - Product Management Feasibility Tool
----------------------------------------------------
Author: Manan Patel
Version: 1.3.0
Description:
    This Streamlit application leverages Google Gemini to translate 
    natural language sales requirements into structured technical engineering 
    tickets, including risk assessment, cost estimation, and session history.
"""
from prompts import get_system_prompt
from utils import clean_json_output, generate_jira_format, parse_cost_avg, convert_currency, create_pdf
import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client, Client
import json
import urllib.parse

# -------------------------------------------------------------
# 1. PAGE CONFIG (Must absolutely be the first Streamlit command)
# -------------------------------------------------------------
st.set_page_config(
        page_title="BridgeBuild AI",
        page_icon="Logo_bg_removed.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# -------------------------------------------------------------
# 2. INITIALIZE SUPABASE
# -------------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# INITIALIZE SESSION STATE
if "history" not in st.session_state:
    st.session_state.history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------------------------------------------
# 3. CUSTOM CSS
# -------------------------------------------------------------
def setup_custom_styling():
    st.markdown("""
    <style>
        /* --- 1. RESET PRIMARY COLOR VARIABLES --- */
        :root {
            --primary-color: #012169;
        }

        /* --- 2. RADIO BUTTONS (The Red Dot) --- */
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
            background-color: #012169 !important;
            border-color: #012169 !important;
        }
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div {
            background-color: white !important;
        }

        /* --- 3. SLIDERS (The Red Line & Handle) --- */
        div[data-baseweb="slider"] div[role="slider"] {
            background-color: #012169 !important;
            box-shadow: none !important;
        }
        div[data-baseweb="slider"] div[data-testid="stTickBar"] > div {
             background-color: #012169 !important;
        }
        div[data-testid="stMarkdownContainer"] p code {
            color: #012169 !important;
        }
        
        /* --- 4. CHECKBOXES --- */
        div[data-baseweb="checkbox"] div[aria-checked="true"] {
            background-color: #012169 !important;
            border-color: #012169 !important;
        }

        /* --- 5. SIDEBAR COMPACTION --- */
        [data-testid="stSidebarUserContent"] {
            padding-top: 0rem !important;
            margin-top: -50px !important;
        }

        /* --- 6. BUTTONS --- */
        div.stButton > button:first-child {
            background-color: #012169;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            padding: 12px 24px;
        }
        div.stButton > button:first-child:hover {
            background-color: #001547;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. LOGIN PAGE (LOCKED - COMPACT & BLUE)
# -------------------------------------------------------------
def login_page():
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            .block-container {
                padding-top: 3rem !important;
                padding-bottom: 0rem !important;
            }
            div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
                background-color: #012169 !important;
                border-color: #012169 !important;
            }
            div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div {
                background-color: white !important;
            }
            div.stButton > button[kind="primary"] {
                background-color: #012169 !important;
                border: none !important;
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: #001547 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        with st.container(border=True):
            c_img1, c_img2, c_img3 = st.columns([1, 1, 0.6])
            with c_img2:
                st.image("Logo_bg_removed.png", width=80)
            
            auth_mode = st.radio("Action:", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
            st.write("")
            
            email = st.text_input("Email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            st.write("") 
            
            if auth_mode == "Log In":
                if st.button("Log In", use_container_width=True, type="primary", key="login_btn"):
                    try:
                        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = response.user
                        st.session_state.logged_in = True
                        st.success("Success! Loading dashboard...")
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e)
                        if "Email not confirmed" in error_msg:
                            st.warning("Please check your inbox and click the confirmation link.")
                        elif "Invalid login credentials" in error_msg:
                            st.error("Incorrect email or password.")
                        else:
                            st.error(f"Login failed: {error_msg}")
                            
            else:
                if st.button("Create Account", use_container_width=True, type="primary", key="signup_btn"):
                    try:
                        response = supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Account created! Please check your email to confirm.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")
            
            st.markdown("<div style='text-align: center; color: grey; font-size: 11px; margin-top: 10px;'>Protected by Enterprise Security</div>", unsafe_allow_html=True)
            
# -------------------------------------------------------------
# 5. MAIN APP
# -------------------------------------------------------------
def main_app():
    setup_custom_styling()
    
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        
        with col_logo:
            st.image("Logo_bg_removed.png", width=40) 
            
        with col_text:
            st.markdown(
                """
                <h3 style='margin: 0; padding-top: 8px; font-size: 18px; color: var(--text-color); font-weight: 600;'>
                    BridgeBuild AI
                </h3>
                """, 
                unsafe_allow_html=True
            )
        st.markdown("---")
        st.header("Configuration")
        
        if "GOOGLE_API_KEY" in st.secrets:
            st.success("✅ API Key Loaded from System")
            api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            api_key = st.text_input("Enter Google Gemini API Key", type="password")
            st.info("Get your free key from aistudio.google.com")
        
        st.divider()
        st.header("Business Settings")
        currency = st.radio("Display Currency:", ["USD ($)", "INR (₹)"])
        rate_type = st.selectbox(
            "Rate Standard:", 
            ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"],
            help="Select the billing rate to adjust cost estimates."
        )
        st.markdown("---")
        model_choice = st.radio(
            "AI Model:", 
            ["Gemini 1.5 Flash (Fast)", "Gemini 1.5 Pro (High Reasoning)"],
            index=0,
            help="Flash is faster/cheaper. Pro is better for complex logic."
        )
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
            
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()

    st.title("BridgeBuild AI")
    st.markdown("### Turn Sales Conversations into Engineering Tickets & Budgets")

    if st.button("Load Sample Email"):
        st.session_state.sales_input = "Client wants a mobile app for food delivery. Needs GPS tracking for drivers, a menu for customers, and a payment gateway. They have a budget of $15k."
    
    if "sales_input" not in st.session_state:
        st.session_state.sales_input = ""

    sales_input = st.text_area("Paste the Client Requirement / Sales Email:", 
        value=st.session_state.sales_input,
        height=150, 
        placeholder="Example: Client wants to merge the weighbridge and gate system...")

    if st.button("Generate Ticket & Budget"):
        if not api_key:
            st.error("Please enter your API Key in the sidebar first!")
        elif not sales_input:
            st.warning("Please enter a sales request.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                SYSTEM_PROMPT = get_system_prompt(rate_type)
                
                with st.spinner("Consulting Engineering & Finance Teams..."):
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"

                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.0,
                            response_mime_type="application/json"
                        ),
                        contents=sales_input
                    )
                    cleaned_text = clean_json_output(response.text)
                    data = json.loads(cleaned_text)

                st.success("Analysis Complete!")

                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)

                st.session_state.history.append({
                    "summary": data.get("summary"),
                    "cost": f"{fmt_low} - {fmt_high}",
                    "raw_cost": raw_cost,  
                    "complexity": data.get("complexity_score"), 
                    "time": data.get("development_time"),
                    "full_data": response.text
                })
                
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Complexity", data.get("complexity_score"))
                with col2: st.metric("Dev Time", data.get("development_time"))
                with col3: st.metric("Est. Budget", f"{fmt_low} - {fmt_high}")
                with col4: st.metric("Risks Detected", len(data.get("technical_risks", [])))

                st.divider()
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.subheader("Engineering Ticket")
                    st.info(f"**Summary:** {data.get('summary')}")
                    
                    st.markdown("Technical Risks")
                    for risk in data.get("technical_risks", []):
                        st.warning(f"- {risk}")
                        
                    st.markdown("🏗 Suggested Tech Stack")
                    st.code("\n".join(data.get("suggested_stack", [])), language="bash")

                with col_right:
                    st.subheader("Data Schema")
                    st.write("Primary Entities:")
                    for entity in data.get("primary_entities", []):
                        st.success(f"🆔 {entity}")
                
                # --- ACTION AREA ---
                st.divider()
                
                col_action1, col_action2 = st.columns([1, 1], gap="medium")
                
                with col_action1:
                    st.markdown("#### 📄 Export Report")
                    st.download_button(
                        label="Download PDF",
                        data=create_pdf(data),
                        file_name="bridgebuild_ticket.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                
                with col_action2:
                    st.markdown("#### ✉️ Share with Team")
                    
                    ticket_name = data.get('ticket_name', data.get('summary', 'New Project'))[:50]
                    if len(data.get('summary', '')) > 50: ticket_name += "..."
                    
                    body_text = f"Hello Engineering Team,\n\n"
                    body_text += f"Please review the following scoped technical requirements from BridgeBuild AI:\n\n"
                    body_text += f"-> TICKET SUMMARY:\n{data.get('summary', 'N/A')}\n\n"
                    body_text += f"-> METRICS:\n"
                    body_text += f"- Complexity: {data.get('complexity_score', 'N/A')}\n"
                    body_text += f"- Est. Dev Time: {data.get('development_time', 'N/A')}\n"
                    body_text += f"- Est. Budget: {fmt_low} - {fmt_high}\n\n"
                    body_text += f"-> SUGGESTED TECH STACK:\n{', '.join(data.get('suggested_stack', []))}\n\n"
                    body_text += f"-> KEY RISKS:\n"
                    for risk in data.get('technical_risks', [])[:3]: 
                        body_text += f"- {risk}\n"
                    
                    body_text += "\nFull acceptance criteria and data schema are attached in the PDF.\n\nBest,\nProduct Management"
                    
                    subject_encoded = urllib.parse.quote(f"Engineering Ticket: {ticket_name}")
                    body_encoded = urllib.parse.quote(body_text)
                    mailto_link = f"mailto:?subject={subject_encoded}&body={body_encoded}"
                    
                    st.markdown(
                        f"""
                        <a href="{mailto_link}" target="_blank" style="text-decoration: none;">
                            <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                                Email to Engineering
                            </button>
                        </a>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    with st.expander("View Jira / Confluence Markup", expanded=False):
                        st.code(generate_jira_format(data), language="jira")
                        st.caption("Copy to paste directly into Jira's description field.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # HISTORY SECTION
    # HISTORY SECTION
    if st.session_state.history:
        st.divider()
        st.subheader("Session History")
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Ticket #{len(st.session_state.history) - i}: {item['summary'][:60]}..."):
                
                # Parse the raw JSON data saved in history
                past_data = json.loads(item['full_data'])
                
                # Layout metrics side-by-side
                hist_col1, hist_col2 = st.columns(2)
                with hist_col1:
                    st.write(f"**Est. Cost:** {item['cost']}")
                with hist_col2:
                    st.write(f"**Timeline:** {item['time']}")
                
                st.write("") # Spacer
                
                # --- PREPARE EMAIL CONTENT ---
                hist_ticket_name = past_data.get('ticket_name', past_data.get('summary', 'Historical Project'))[:50]
                if len(past_data.get('summary', '')) > 50: hist_ticket_name += "..."
                
                hist_body = f"Hello Engineering Team,\n\n"
                hist_body += f"Please review the following scoped technical requirements from BridgeBuild AI (Historical Record):\n\n"
                hist_body += f"-> TICKET SUMMARY:\n{past_data.get('summary', 'N/A')}\n\n"
                hist_body += f"-> METRICS:\n"
                hist_body += f"- Complexity: {past_data.get('complexity_score', 'N/A')}\n"
                hist_body += f"- Est. Dev Time: {past_data.get('development_time', 'N/A')}\n"
                hist_body += f"- Est. Budget: {item['cost']}\n\n"  # Grabs the formatted cost directly from history
                hist_body += f"-> SUGGESTED TECH STACK:\n{', '.join(past_data.get('suggested_stack', []))}\n\n"
                hist_body += f"-> KEY RISKS:\n"
                for risk in past_data.get('technical_risks', [])[:3]: 
                    hist_body += f"- {risk}\n"
                
                hist_body += "\nFull acceptance criteria and data schema are attached in the PDF.\n\nBest,\nProduct Management"
                
                hist_subj_enc = urllib.parse.quote(f"Engineering Ticket: {hist_ticket_name}")
                hist_body_enc = urllib.parse.quote(hist_body)
                hist_mailto = f"mailto:?subject={hist_subj_enc}&body={hist_body_enc}"

                # --- SIDE-BY-SIDE ACTION BUTTONS ---
                hist_btn_col1, hist_btn_col2 = st.columns(2)
                
                with hist_btn_col1:
                    st.download_button(
                        label="Download PDF",
                        data=create_pdf(past_data),
                        file_name=f"ticket_history_{i}.pdf",
                        mime="application/pdf",
                        key=f"history_btn_{i}",
                        use_container_width=True
                    )
                
                with hist_btn_col2:
                    st.markdown(
                        f"""
                        <a href="{hist_mailto}" target="_blank" style="text-decoration: none;">
                            <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                                Email Team
                            </button>
                        </a>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.write("") # Spacer before Jira
                
                # Jira Markup expander
                with st.expander("View Jira / Confluence Markup", expanded=False):
                    st.code(generate_jira_format(past_data), language="jira")
                    st.caption("Copy this historical record for your Jira board.")
    
    st.markdown("---")
    footer_html = """
    <div style='text-align: center; color: #666666; font-size: 0.8em; font-family: sans-serif;'>
        <p>
            Built by <a href='https://github.com/mananp-2730' target='_blank' style='text-decoration: none; color: #0366d6;'>Manan Patel</a>
            &nbsp;|&nbsp;
            <a href='https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool' target='_blank' style='text-decoration: none; color: #0366d6;'>View Source Code</a>
        </p>
        <p style='font-size: 0.7em; margin-top: -10px;'>Powered by Google Gemini and Supabase Authentication.</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# -------------------------------------------------------------
# 6. ROUTING LOGIC
# -------------------------------------------------------------
if st.session_state.logged_in:
    main_app()
else:
    login_page()
