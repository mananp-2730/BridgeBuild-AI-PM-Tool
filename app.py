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
        /* --- 7. METRIC COLOR FIX --- */
        /* Forces the metric values to stay pure white/black instead of inheriting primary blue */
        [data-testid="stMetricValue"] {
            color: var(--text-color) !important;
        }
        [data-testid="stMetricValue"] > div {
            color: var(--text-color) !important;
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
        # Load the API key for backend use
        api_key = st.secrets.get("GOOGLE_API_KEY")
        st.write("")
        
        # --- FETCH USER PROFILE PREFERENCES ---
        if "user_prefs" not in st.session_state:
            try:
                user_id = st.session_state.user.id
                profile_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
                
                if profile_res.data:
                    st.session_state.user_prefs = profile_res.data[0]
                else:
                    # Create default profile if they are a new user
                    default_prefs = {
                        "id": user_id,
                        "currency": "USD ($)",
                        "rate_standard": "US Agency ($150/hr)",
                        "ai_model": "Gemini 1.5 Flash (Fast)"
                    }
                    supabase.table("profiles").insert(default_prefs).execute()
                    st.session_state.user_prefs = default_prefs
            except Exception as e:
                # Fallback if DB fails
                st.session_state.user_prefs = {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)"}

        # Safe list options
        curr_opts = ["USD ($)", "INR (₹)"]
        rate_opts = ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"]
        model_opts = ["Gemini 1.5 Flash (Fast)", "Gemini 1.5 Pro (High Reasoning)"]

        # Safely find the index of their saved preference (defaults to 0 if not found)
        curr_pref = st.session_state.user_prefs.get("currency", "USD ($)")
        curr_idx = curr_opts.index(curr_pref) if curr_pref in curr_opts else 0
        
        rate_pref = st.session_state.user_prefs.get("rate_standard", "US Agency ($150/hr)")
        rate_idx = rate_opts.index(rate_pref) if rate_pref in rate_opts else 0
        
        model_pref = st.session_state.user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")
        model_idx = model_opts.index(model_pref) if model_pref in model_opts else 0

        st.divider()
        # --- SIDEBAR UI ---
        st.header("Business Settings")
        
        currency = st.radio("Display Currency:", curr_opts, index=curr_idx)
        rate_type = st.selectbox(
            "Rate Standard:", 
            rate_opts, 
            index=rate_idx,
            help="Select the billing rate to adjust cost estimates."
        )
        model_choice = st.radio(
            "AI Model:", 
            model_opts, 
            index=model_idx,
            help="Flash is faster/cheaper. Pro is better for complex logic."
        )
        
        # --- SAVE SETTINGS BUTTON ---
        if st.button("Save Settings", use_container_width=True):
            new_prefs = {
                "currency": currency,
                "rate_standard": rate_type,
                "ai_model": model_choice
            }
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
                user_id = st.session_state.user.id
                # Delete all rows where the user_id matches the logged-in user
                supabase.table("tickets").delete().eq("user_id", user_id).execute()
                st.success("Database History Cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to clear history: {str(e)}")

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

    # --- 1. SESSION STATE FOR ACTIVE TICKET ---
    if "active_ticket" not in st.session_state:
        st.session_state.active_ticket = None
    if "active_ticket_id" not in st.session_state:
        st.session_state.active_ticket_id = None

    # --- 2. GENERATION LOGIC ---
    if st.button("Generate Ticket & Budget"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline. Please contact support.")
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

                # Save to Session State (Memory)
                st.session_state.active_ticket = data
                st.success("Analysis Complete!")

                # Calculate formatted costs
                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)

                # --- SAVE INITIAL DRAFT TO SUPABASE ---
                user_id = st.session_state.user.id
                new_ticket = {
                    "user_id": user_id,
                    "summary": data.get("summary"),
                    "cost": f"{fmt_low} - {fmt_high}",
                    "raw_cost": raw_cost,  
                    "complexity": data.get("complexity_score"), 
                    "time": data.get("development_time"),
                    "full_data": response.text
                }
                db_res = supabase.table("tickets").insert(new_ticket).execute()
                # Save the database ID so we can update it if the user iterates
                st.session_state.active_ticket_id = db_res.data[0]['id']
                
                st.rerun() # Force a UI refresh to show the new ticket

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # --- 3. DISPLAY & ITERATE ACTIVE TICKET ---
    if st.session_state.active_ticket:
        data = st.session_state.active_ticket
        
        # Recalculate costs for display based on current currency setting
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
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("Engineering Ticket")
            st.info(f"**Summary:** {data.get('summary')}")
            
            # --- NEW: AGILE MVP PHASING UI ---
            st.markdown("### Phase 1: Core MVP")
            
            # Smart Check: If it's a new Agile ticket, show stories. If it's an old ticket, show bullet points.
            if "mvp_user_stories" in data:
                for item in data.get("mvp_user_stories", []):
                    with st.expander(f" {item.get('story', 'User Story')}", expanded=False):
                        st.markdown("**Acceptance Criteria:**")
                        for ac in item.get("acceptance_criteria", []):
                            st.markdown(f"- {ac}")
            else:
                for feat in data.get("mvp_features", []):
                    st.markdown(f"- {feat}")
                
            st.markdown("### Phase 2: Future Enhancements")
            
            # Convert Phase 2 Budget Currency
            p2_raw = data.get("phase_2_budget_usd", "0-0")
            p2_low = p2_raw.split("-")[0] if "-" in p2_raw else p2_raw
            p2_high = p2_raw.split("-")[1] if "-" in p2_raw else p2_raw
            p2_fmt_low = convert_currency(p2_low, currency)
            p2_fmt_high = convert_currency(p2_high, currency)
            
            st.caption(f"**Est. Extra Time:** {data.get('phase_2_time', 'N/A')} | **Est. Extra Budget:** {p2_fmt_low} - {p2_fmt_high}")
            for feat in data.get("phase_2_features", []):
                st.markdown(f"- {feat}")
            # ---------------------------
            
            st.markdown("### Technical Risks")
            for risk in data.get("technical_risks", []):
                st.warning(f"- {risk}")
                
            st.markdown("### Suggested Tech Stack")
            st.code("\n".join(data.get("suggested_stack", [])), language="bash")

        with col_right:
            st.subheader("Data Schema")
            st.write("Primary Entities:")
            for entity in data.get("primary_entities", []):
                st.success(f"🆔 {entity}")
        
        # --- EXPORT ACTIONS ---
        # --- EXPORT ACTIONS ---
        st.divider()
        col_action1, col_action2 = st.columns([1, 1], gap="medium")
        
        with col_action1:
            st.markdown("#### Export PDF Reports")
            # Button 1: Detailed (Eng)
            st.download_button(
                label="Download Detailed Ticket (Engineering)",
                data=create_pdf(data, currency, ticket_type="detailed"),
                file_name="bridgebuild_detailed_ticket.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            # Button 2: Brief (Sales)
            st.download_button(
                label="Download Brief Summary (Sales / Client)",
                data=create_pdf(data, currency, ticket_type="brief"),
                file_name="bridgebuild_brief_summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        
        with col_action2:
            st.markdown("#### Share with Stakeholders")
            ticket_name = data.get('ticket_name', data.get('summary', 'New Project'))[:50]
            
            # --- EMAIL 1: ENGINEERING (Highly Technical) ---
            eng_body = f"Hello Engineering Team,\n\nPlease review the scoped Agile requirements from BridgeBuild AI:\n\n"
            eng_body += f"-> SUMMARY:\n{data.get('summary', 'N/A')}\n\n"
            eng_body += f"-> PHASE 1: CORE MVP (Agile Stories)\n"
            eng_body += f"- Est. Dev Time: {data.get('development_time', 'N/A')}\n"
            eng_body += f"- Est. Budget: {fmt_low} - {fmt_high}\n\n"
            if "mvp_user_stories" in data:
                for item in data.get('mvp_user_stories', []):
                    eng_body += f"~ {item.get('story')}\n"
                    for ac in item.get('acceptance_criteria', []):
                        eng_body += f"   * AC: {ac}\n"
                    eng_body += "\n"
            else:
                for feat in data.get('mvp_features', []):
                    eng_body += f"  * {feat}\n"
                    
            eng_body += f"\n-> PHASE 2: FUTURE ENHANCEMENTS\n"
            for feat in data.get('phase_2_features', []): eng_body += f"  * {feat}\n"
            eng_body += f"\n-> OVERVIEW & STACK:\n- Complexity: {data.get('complexity_score', 'N/A')}\n- Stack: {', '.join(data.get('suggested_stack', []))}\n\n"
            eng_body += f"-> KEY RISKS:\n"
            for risk in data.get('technical_risks', [])[:3]: eng_body += f"- {risk}\n"
            eng_body += "\nBest,\nProduct Management"
            
            eng_subj_enc = urllib.parse.quote(f"Eng Ticket: {ticket_name}")
            eng_body_enc = urllib.parse.quote(eng_body)
            eng_mailto = f"mailto:?subject={eng_subj_enc}&body={eng_body_enc}"
            
            # --- EMAIL 2: SALES (Client-Friendly) ---
            sales_body = f"Hello Sales Team,\n\nGreat news—we have completed the initial feasibility scoping for the client request. Here is the high-level breakdown you can use to guide your conversation and manage expectations.\n\n"
            sales_body += f"-> PROJECT GOAL:\n{data.get('summary', 'N/A')}\n\n"
            sales_body += f"-> PHASE 1: CORE MVP (Initial Deliverable)\n"
            sales_body += f"- Estimated Timeline: {data.get('development_time', 'N/A')}\n"
            sales_body += f"- Estimated Budget: {fmt_low} - {fmt_high}\n\n"
            sales_body += "Key Capabilities Included:\n"
            if "mvp_user_stories" in data:
                for item in data.get('mvp_user_stories', []): sales_body += f"  * {item.get('story')}\n"
            else:
                for feat in data.get('mvp_features', []): sales_body += f"  * {feat}\n"
                
            sales_body += f"\n-> PHASE 2: FUTURE ENHANCEMENTS (Upsell Opportunities)\n"
            sales_body += f"- Est. Extra Time: {data.get('phase_2_time', 'N/A')}\n"
            sales_body += f"- Est. Extra Budget: {p2_fmt_low} - {p2_fmt_high}\n"
            for feat in data.get('phase_2_features', []): sales_body += f"  * {feat}\n"
            
            sales_body += f"\n-> BUSINESS CONSIDERATIONS:\n"
            for risk in data.get('technical_risks', [])[:2]: sales_body += f"- {risk}\n"
            sales_body += "\nLet me know if the client approves this Phase 1 budget range so we can begin formal sprint planning!\n\nBest,\nProduct Management"
            
            sales_subj_enc = urllib.parse.quote(f"Sales Scoping: {ticket_name}")
            sales_body_enc = urllib.parse.quote(sales_body)
            sales_mailto = f"mailto:?subject={sales_subj_enc}&body={sales_body_enc}"
            
            # Render Buttons
            st.markdown(
                f"""
                <a href="{eng_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-bottom: 10px;">Email to Engineering</button>
                </a>
                <a href="{sales_mailto}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #2E7D32; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer;">Email to Sales</button>
                </a>
                """, unsafe_allow_html=True
            )
            
            with st.expander("View Jira / Confluence Markup", expanded=False):
                st.code(generate_jira_format(data, currency), language="jira")
                
        # --- 4. THE ITERATION ENGINE (AI CHAT) ---
        st.divider()
        st.subheader("🔄 Refine this Ticket")
        refine_query = st.chat_input("E.g., Add a risk about third-party API rate limits...")
        
        if refine_query:
            if not api_key:
                st.error("API Key missing.")
            else:
                with st.spinner("AI is updating the ticket..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                        
                        # Tell Gemini to update the existing JSON
                        update_prompt = f"""
                        You are a Technical Product Manager. Update the following JSON ticket based on the user's request.
                        You MUST return the exact same JSON schema structure, just with updated values.
                        
                        CURRENT TICKET:
                        {json.dumps(data)}
                        
                        USER REQUEST:
                        {refine_query}
                        """
                        
                        update_response = client.models.generate_content(
                            model=model_id, 
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                response_mime_type="application/json"
                            ),
                            contents=update_prompt
                        )
                        
                        updated_data = json.loads(clean_json_output(update_response.text))
                        
                        # 1. Update Streamlit Memory
                        st.session_state.active_ticket = updated_data
                        
                        # 2. Update Supabase Database Row
                        if st.session_state.active_ticket_id:
                            supabase.table("tickets").update({
                                "summary": updated_data.get("summary"),
                                "complexity": updated_data.get("complexity_score"),
                                "time": updated_data.get("development_time"),
                                "full_data": update_response.text
                            }).eq("id", st.session_state.active_ticket_id).execute()
                            
                        st.rerun() # Refresh UI with new data
                        
                    except Exception as e:
                        st.error(f"Failed to refine: {str(e)}")

    # HISTORY SECTION
    # --- HISTORY SECTION (Now fetching from Supabase!) ---
    st.divider()
    st.subheader("Saved Tickets History")
    
    try:
        # 1. Fetch data from Supabase, ordered by newest first
        user_id = st.session_state.user.id
        db_response = supabase.table("tickets").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        saved_tickets = db_response.data
        
        # 2. Display the tickets
        if saved_tickets:
            for i, item in enumerate(saved_tickets):
                with st.expander(f"Ticket: {item['summary'][:60]}..."):
                    
                    past_data = json.loads(item['full_data'])
                    
                    hist_col1, hist_col2 = st.columns(2)
                    with hist_col1:
                        st.write(f"**Est. Cost:** {item['cost']}")
                    with hist_col2:
                        st.write(f"**Timeline:** {item['time']}")
                    
                    st.write("") 
                    
                    # --- PREPARE FULL EMAIL CONTENT FOR HISTORY ---
                    hist_ticket_name = past_data.get('ticket_name', past_data.get('summary', 'Historical Project'))[:50]
                    if len(past_data.get('summary', '')) > 50: hist_ticket_name += "..."
                    
                    hist_body = f"Hello Team,\n\n"
                    hist_body += f"Please review the historical scoped requirements and phased approach:\n\n"
                    hist_body += f"-> SUMMARY:\n{past_data.get('summary', 'N/A')}\n\n"
                    
                    hist_body += f"-> PHASE 1: CORE MVP\n"
                    hist_body += f"- Est. Dev Time: {item['time']}\n"
                    hist_body += f"- Est. Budget: {item['cost']}\n"
                    for feat in past_data.get('mvp_features', []):
                        hist_body += f"  * {feat}\n"
                    
                    hist_body += f"\n-> PHASE 2: FUTURE ENHANCEMENTS\n"
                    hist_body += f"- Est. Extra Time: {past_data.get('phase_2_time', 'N/A')}\n"
                    hist_body += f"- Est. Extra Budget (USD Raw): ${past_data.get('phase_2_budget_usd', 'N/A')}\n"
                    for feat in past_data.get('phase_2_features', []):
                        hist_body += f"  * {feat}\n"
                        
                    hist_body += f"\n-> OVERVIEW & STACK:\n"
                    hist_body += f"- Complexity: {past_data.get('complexity_score', 'N/A')}\n"
                    hist_body += f"- Suggested Stack: {', '.join(past_data.get('suggested_stack', []))}\n\n"
                    
                    hist_body += f"-> KEY RISKS:\n"
                    for risk in past_data.get('technical_risks', [])[:3]:
                        hist_body += f"- {risk}\n"
                    
                    hist_body += "\nFull data schema is attached in the PDF.\n\nBest,\nProduct Management"
                    
                    hist_subj_enc = urllib.parse.quote(f"Engineering Ticket: {hist_ticket_name}")
                    hist_body_enc = urllib.parse.quote(hist_body)
                    hist_mailto = f"mailto:?subject={hist_subj_enc}&body={hist_body_enc}"

                    hist_btn_col1, hist_btn_col2 = st.columns(2)
                    with hist_btn_col1:
                        st.download_button(
                            label="Download PDF",
                            data=create_pdf(past_data, currency),
                            file_name=f"ticket_{item['id'][:8]}.pdf",
                            mime="application/pdf",
                            key=f"hist_pdf_{item['id']}",
                            use_container_width=True
                        )
                    with hist_btn_col2:
                        st.markdown(
                            f"""<a href="{hist_mailto}" target="_blank" style="text-decoration: none;">
                                <button style="width: 100%; background-color: #012169; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer;">✉️ Email Team</button>
                            </a>""", unsafe_allow_html=True
                        )
                    
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
