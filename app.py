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
import json

# Custom CSS
def setup_custom_styling():
    st.markdown("""
    <style>
        /* --- 1. RESET PRIMARY COLOR VARIABLES --- */
        :root {
            --primary-color: #012169;
        }

        /* --- 2. RADIO BUTTONS (The Red Dot) --- */
        /* Forces the selected radio button to be Duke Blue */
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
            background-color: #012169 !important;
            border-color: #012169 !important;
        }
        /* Ensure the dot inside is white */
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div {
            background-color: white !important;
        }

        /* --- 3. SLIDERS (The Red Line & Handle) --- */
        /* The draggable handle */
        div[data-baseweb="slider"] div[role="slider"] {
            background-color: #012169 !important;
            box-shadow: none !important;
        }
        /* The filled track line */
        div[data-baseweb="slider"] div[data-testid="stTickBar"] > div {
             background-color: #012169 !important;
        }
        /* The value text (e.g., "0.70") which is usually red */
        div[data-testid="stMarkdownContainer"] p code {
            color: #012169 !important;
        }
        
        /* --- 4. CHECKBOXES --- */
        div[data-baseweb="checkbox"] div[aria-checked="true"] {
            background-color: #012169 !important;
            border-color: #012169 !important;
        }

        /* --- 5. SIDEBAR COMPACTION (Keep this!) --- */
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
    
# PAGE CONFIG (Must be the first Streamlit command)
st.set_page_config(
        page_title="BridgeBuild AI",
        page_icon="Logo_bg_removed.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# INITIALIZE SESSION STATE
if "history" not in st.session_state:
    st.session_state.history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN PAGE ---
# --- LOGIN PAGE ---
def login_page():
    # 1. SETUP: Hide Sidebar & Fix global padding for this page
    st.markdown("""
        <style>
            /* Hide the actual sidebar navigation on the login page */
            [data-testid="stSidebar"] { display: none; }
            
            /* Minimize top padding so content starts higher up */
            .block-container { 
                padding-top: 1rem; 
                padding-bottom: 0rem; 
                max-width: 100%; /* Ensure full width utilization */
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. CSS for the Hero Image (Right Column Fixes)
    # This is crucial to make the image look like a "cover" background
    st.markdown("""
        <style>
            /* Target the image inside the second main column */
            div[data-testid="column"]:nth-of-type(2) div[data-testid="stImage"] > img {
                height: 92vh;            /* Force it to fill most of the vertical height */
                object-fit: cover;       /* CROP the image so it doesn't stretch or squish */
                border-radius: 16px;     /* Adds a modern rounded corner touch */
            }
        </style>
    """, unsafe_allow_html=True)

    # 3. SPLIT LAYOUT: Left (Form) vs Right (Hero Image)
    # Use a [1, 1.6] ratio to give the image slightly more visual weight
    col1, col2 = st.columns([1, 1.6], gap="large")
    
    # --- LEFT COLUMN: The Login Form ---
    with col1:
        # Spacers to push the form down visually for centering
        st.write("")
        st.write("")
        st.write("")
        
        # BRANDING
        brand_col1, brand_col2 = st.columns([0.2, 1.1])
        with brand_col1:
            # Make sure "Logo_bg_removed.png" is in your project folder
            st.image("Logo_bg_removed.png", width=60)
        with brand_col2:
            # var(--text-color) adapts automatically to Light/Dark mode
            st.markdown(
                """
                <h2 style='color: var(--text-color); margin: 0; padding-top: 10px; font-weight: 700; font-size: 28px;'>
                    BridgeBuild AI
                </h2>
                """, 
                unsafe_allow_html=True
            )
        st.write("")
        
        # INPUTS
        username = st.text_input("Email", placeholder="name@company.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.write("") # Tiny spacer
        
        # BUTTON
        if st.button("Sign In  ➔", use_container_width=True):
            # HARDCODED CREDENTIALS
            if username == "admin" and password == "bridge123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

        # FOOTER
        st.markdown(
            """
            <div style='margin-top: 50px; font-size: 12px; color: #888;'>
                Protected by Enterprise Security. <br>
                <a href='#' style='color: gray; text-decoration: none;'>Forgot Password?</a>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # --- RIGHT COLUMN: The Abstract Structure Hero Image ---
    with col2:
        # Image selection: Abstract modern architecture with blue tones.
        # Credit: Simone Hutsch via Unsplash
        st.image(
            "Image.jpg", 
            use_container_width=True
        )

# --- MAIN APP ---
def main_app():
    setup_custom_styling()
    # SIDEBAR: CONFIGURATION
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        
        with col_logo:
            # Logo.jpeg (The small square icon)
            st.image("Logo_bg_removed.png", width=40) 
            
        with col_text:
            # CHANGED: 'color: #012169' -> 'color: var(--text-color)'
            # This makes it Black in Light Mode and White in Dark Mode automatically.
            st.markdown(
                """
                <h3 style='margin: 0; padding-top: 8px; font-size: 18px; color: var(--text-color); font-weight: 600;'>
                    BridgeBuild
                </h3>
                """, 
                unsafe_allow_html=True
            )
        st.markdown("---")
        st.header("Configuration")
        
        # 1. API Key Logic
        if "GOOGLE_API_KEY" in st.secrets:
            st.success("✅ API Key Loaded from System")
            api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            api_key = st.text_input("Enter Google Gemini API Key", type="password")
            st.info("Get your free key from aistudio.google.com")
        
        # 3. Business Settings (ALWAYS VISIBLE)
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
        # LOGOUT BUTTON
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
            
        # CLEAR HISTORY BUTTON
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()

    # APP HEADER
    st.title("BridgeBuild AI")
    st.markdown("### Turn Sales Conversations into Engineering Tickets & Budgets")

    # INPUT AREA
    # Add a button to load sample data
    #sales_input = st.text_area("Paste the Client Requirement / Sales Email:", height=150, 
        #placeholder="Example: Client wants to merge the weighbridge and gate system...")
    if st.button("Load Sample Email"):
        st.session_state.sales_input = "Client wants a mobile app for food delivery. Needs GPS tracking for drivers, a menu for customers, and a payment gateway. They have a budget of $15k."
    
    # Use session state to hold the input value
    if "sales_input" not in st.session_state:
        st.session_state.sales_input = ""

    sales_input = st.text_area("Paste the Client Requirement / Sales Email:", 
        value=st.session_state.sales_input,
        height=150, 
        placeholder="Example: Client wants to merge the weighbridge and gate system...")

    # THE LOGIC
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
                    # SAFE MODEL IDS
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

                # CALCULATE COSTS
                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)

                # SAVE TO HISTORY (With raw_cost for charts)
                st.session_state.history.append({
                    "summary": data.get("summary"),
                    "cost": f"{fmt_low} - {fmt_high}",
                    "raw_cost": raw_cost,  
                    "complexity": data.get("complexity_score"), 
                    "time": data.get("development_time"),
                    "full_data": response.text
                })
                
                # METRICS ROW
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("Complexity", data.get("complexity_score"))
                with col2: st.metric("Dev Time", data.get("development_time"))
                with col3: st.metric("Est. Budget", f"{fmt_low} - {fmt_high}")
                with col4: st.metric("Risks Detected", len(data.get("technical_risks", [])))

                # DETAILED TICKET
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
                
               # PDF EXPORT
               # --- ACTION AREA ---
                st.divider()
                
                # Create two columns for the export actions
                col_action1, col_action2 = st.columns([1, 1], gap="medium")
                
                with col_action1:
                    st.markdown("#### 📄 Export Report")
                    # Uses your updated utils.create_pdf function
                    st.download_button(
                        label="Download Professional PDF",
                        data=create_pdf(data),
                        file_name="bridgebuild_ticket.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        icon="📥"
                    )
                
                with col_action2:
                    st.markdown("#### 🎫 Jira Integration")
                    with st.expander("View Jira / Confluence Markup", expanded=False):
                        st.code(generate_jira_format(data), language="jira")
                        st.caption("Copy this text and paste it directly into Jira's description field.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # HISTORY SECTION
    if st.session_state.history:
        st.divider()
        st.subheader("Session History")
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Ticket #{len(st.session_state.history) - i}: {item['summary'][:60]}..."):
                st.write(f"**Est. Cost:** {item['cost']}")
                st.write(f"**Timeline:** {item['time']}")
                st.download_button(
                    label="Download PDF Record",
                    data=create_pdf(json.loads(item['full_data'])),
                    file_name=f"ticket_history_{i}.pdf",
                    mime="application/pdf",
                    key=f"history_btn_{i}"
                )
    
    # --- FOOTER (Professional HTML) ---
    st.markdown("---")
    footer_html = """
    <div style='text-align: center; color: #666666; font-size: 0.8em; font-family: sans-serif;'>
        <p>
            Built by <a href='https://github.com/mananp-2730' target='_blank' style='text-decoration: none; color: #0366d6;'>Manan Patel</a>
            &nbsp;|&nbsp;
            <a href='https://github.com/mananp-2730/BridgeBuild-AI-PM-Tool' target='_blank' style='text-decoration: none; color: #0366d6;'>View Source Code</a>
        </p>
        <p style='font-size: 0.7em; margin-top: -10px;'>Please note: This is a portfolio project using simulated login credentials.</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# --- ROUTING LOGIC ---
if st.session_state.logged_in:
    main_app()
else:
    login_page()
