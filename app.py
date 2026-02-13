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
from utils import convert_currency, create_pdf, generate_jira_format, parse_cost_avg
from fpdf import FPDF
import streamlit as st
from google import genai
from google.genai import types
import json

# PAGE CONFIG (Must be the first Streamlit command)
st.set_page_config(page_title="BridgeBuild AI", page_icon="🌉", layout="wide")

# INITIALIZE SESSION STATE
if "history" not in st.session_state:
    st.session_state.history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- LOGIN PAGE ---
def login_page():
    st.title("BridgeBuild AI Login")
    st.markdown("Please sign in to access the Product Management Tool.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            # HARDCODED CREDENTIALS (Simulation)
            if username == "admin" and password == "bridge123":
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- MAIN APP ---
def main_app():
    # SIDEBAR: CONFIGURATION
    with st.sidebar:
        st.header("Configuration")
        
        # 1. API Key Logic
        if "GOOGLE_API_KEY" in st.secrets:
            st.success("✅ API Key Loaded from System")
            api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            api_key = st.text_input("Enter Google Gemini API Key", type="password")
            st.info("Get your free key from aistudio.google.com")

        # 2. Analytics Dashboard (Only shows if history exists)
        if st.session_state.history:
            st.divider()
            st.markdown("📊 Cost Trends")

            # Extract data for the chart
            chart_data = [parse_cost_avg(item.get('raw_cost', '0')) for item in st.session_state.history]

            # Show a Line Chart
            st.line_chart(chart_data)
            st.caption("Estimated Cost (USD) per Ticket Generated")
        
        # 3. Business Settings (ALWAYS VISIBLE)
        st.divider()
        st.header("Business Settings")
        currency = st.radio("Display Currency:", ["USD ($)", "INR (₹)"])
        rate_type = st.selectbox(
            "Rate Standard:", 
            ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"],
            help="Select the billing rate to adjust cost estimates."
        )
        
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
                            temperature=0.7,
                            response_mime_type="application/json"
                        ),
                        contents=sales_input
                    )
                    
                    data = json.loads(response.text)

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
                    st.subheader("📋 Engineering Ticket")
                    st.info(f"**Summary:** {data.get('summary')}")
                    
                    st.markdown("⚠️ Technical Risks")
                    for risk in data.get("technical_risks", []):
                        st.warning(f"- {risk}")
                        
                    st.markdown("🏗 Suggested Tech Stack")
                    st.code("\n".join(data.get("suggested_stack", [])), language="bash")

                with col_right:
                    st.subheader("💾 Data Schema")
                    st.write("Primary Entities:")
                    for entity in data.get("primary_entities", []):
                        st.success(f"🆔 {entity}")
                
                # PDF EXPORT
                st.divider()
                st.download_button(
                    label="📄 Download Specs as PDF",
                    data=create_pdf(response.text),
                    file_name="project_specs.pdf",
                    mime="application/pdf"
                )
                # JIRA EXPORT
                with st.expander("🛠️ View Jira-Format Ticket"):
                    st.code(generate_jira_format(data), language="jira")
                    st.info("Copy the text above and paste it directly into a Jira Ticket description!")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # HISTORY SECTION
    if st.session_state.history:
        st.divider()
        st.subheader("📜 Session History")
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Ticket #{len(st.session_state.history) - i}: {item['summary'][:60]}..."):
                st.write(f"**Est. Cost:** {item['cost']}")
                st.write(f"**Timeline:** {item['time']}")
                st.download_button(
                    label="Download PDF Record",
                    data=create_pdf(item['full_data']),
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
