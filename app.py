"""
BridgeBuild AI - Product Management Feasibility Tool
----------------------------------------------------
Author: Manan Patel
Version: 1.2.0
Description:
    This Streamlit application leverages Google Gemini to translate 
    natural language sales requirements into structured technical engineering 
    tickets, including risk assessment, cost estimation, and session history.
"""
from fpdf import FPDF
import streamlit as st
from google import genai
from google.genai import types
import json

# INITIALIZE SESSION STATE (HISTORY)
if "history" not in st.session_state:
    st.session_state.history = []

# PAGE CONFIG
st.set_page_config(page_title="BridgeBuild AI", page_icon="🌉", layout="wide")

# SIDEBAR: CONFIGURATION
with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    st.divider()
    st.header("🌍 Business Settings")
    currency = st.radio("Display Currency:", ["USD ($)", "INR (₹)"])
    rate_type = st.selectbox("Rate Standard:", ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"])
    
    # NEW: Model Selection
    model_choice = st.radio(
        "AI Model:", 
        ["Gemini 1.5 Flash (Fast)", "Gemini 1.5 Pro (High Reasoning)"],
        index=0
    )
    # CLEAR HISTORY BUTTON
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun() # Force a rerun to update the UI immediately
    st.info("Get your free key from aistudio.google.com")

# APP HEADER
st.title("🌉 BridgeBuild AI")
st.markdown("### Turn Sales Conversations into Engineering Tickets & Budgets")

# INPUT AREA
sales_input = st.text_area("Paste the Client Requirement / Sales Email:", height=150, 
    placeholder="Example: Client wants to merge the weighbridge and gate system...")

# HELPER: CURRENCY CONVERTER
def convert_currency(usd_amount_str, target_currency):
    try:
        # Extract number from string like "$50,000" -> 50000
        clean_amount = int(usd_amount_str.replace("$", "").replace(",", "").replace("-", "0").split(" ")[0])
        
        if target_currency == "USD ($)":
            return f"${clean_amount:,}"
        else:
            # Approx conversion rate 1 USD = 85 INR
            inr_amount = clean_amount * 85
            return f"₹{inr_amount:,}"
    except:
        return usd_amount_str # Return original if parsing fails

# HELPER: PDF GENERATOR
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Clean text to remove unsupported unicode characters (emojis, etc.)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

# HELPER: JIRA FORMATTER
def generate_jira_format(data):
    jira_text = f"""
h1. {data.get('summary')}

h2. Overview
* **Complexity:** {data.get('complexity_score')}
* **Est. Time:** {data.get('development_time')}
* **Est. Budget:** {data.get('budget_estimate_usd')}

h2. Technical Risks
{{panel:title=Risks|borderStyle=dashed|borderColor=#ff0000}}
{chr(10).join([f'- {risk}' for risk in data.get('technical_risks', [])])}
{{panel}}

h2. Tech Stack
{{code:bash}}
{chr(10).join(data.get('suggested_stack', []))}
{{code}}

h2. Data Schema
||Entity Name||
{chr(10).join([f'|{entity}|' for entity in data.get('primary_entities', [])])}
    """
    return jira_text
# THE LOGIC
if st.button("Generate Ticket & Budget 🚀"):
    if not api_key:
        st.error("Please enter your API Key in the sidebar first!")
    elif not sales_input:
        st.warning("Please enter a sales request.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            # UPDATED PROMPT WITH BUSINESS LOGIC
            SYSTEM_PROMPT = f"""
            You are a Senior Technical Product Manager. Translate Sales requests into Engineering Requirements AND Business Estimates.
            
            Based on the selected rate standard: {rate_type}, estimate the cost accordingly.
            
            Output must be a pure JSON object with these keys:
            - "summary": (String) 1-sentence technical summary.
            - "complexity_score": (String) "Low", "Medium", or "High".
            - "primary_entities": (List) Key data objects.
            - "technical_risks": (List) Potential blockers.
            - "suggested_stack": (List) Specific technologies (e.g., 'Django', 'PostgreSQL').
            - "development_time": (String) Estimated time (e.g., "4-6 Weeks").
            - "budget_estimate_usd": (String) Estimated cost range in USD (e.g., "5000-8000"). Just numbers, no symbols.
            """
            
            with st.spinner("Consulting Engineering & Finance Teams..."):
                # SELECT MODEL BASED ON USER CHOICE
                model_id = "gemini-flash-latest" if "Flash" in model_choice else "gemini-pro-latest"

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

            # DISPLAY RESULTS
            st.success("Analysis Complete!")

            # --- CALCULATE COSTS FIRST ---
            raw_cost = data.get("budget_estimate_usd", "0-0")
            low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
            high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
            
            fmt_low = convert_currency(low_end, currency)
            fmt_high = convert_currency(high_end, currency)

            # --- SAVE TO HISTORY ---
            st.session_state.history.append({
                "summary": data.get("summary"),
                "cost": f"{fmt_low} - {fmt_high}",
                "time": data.get("development_time"),
                "full_data": response.text # Save raw data for later
            })
            
            # 1. METRICS ROW
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Complexity", data.get("complexity_score"))
            with col2:
                st.metric("Dev Time", data.get("development_time"))
            with col3:
                st.metric("Est. Budget", f"{fmt_low} - {fmt_high}")
            with col4:
                st.metric("Risks Detected", len(data.get("technical_risks", [])))

            # 2. DETAILED TICKET
            st.divider()
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.subheader("📋 Engineering Ticket")
                st.info(f"**Summary:** {data.get('summary')}")
                
                st.markdown("#### ⚠️ Technical Risks")
                for risk in data.get("technical_risks", []):
                    st.warning(f"- {risk}")
                    
                st.markdown("#### 🏗 Suggested Tech Stack")
                st.code("\n".join(data.get("suggested_stack", [])), language="bash")

            with col_right:
                st.subheader("💾 Data Schema")
                st.write("Primary Entities:")
                for entity in data.get("primary_entities", []):
                    st.success(f"🆔 {entity}")
            
            # --- PDF Export Feature ---
            st.divider()
            st.download_button(
                label="📄 Download Specs as PDF",
                data=create_pdf(response.text),
                file_name="project_specs.pdf",
                mime="application/pdf"
            )
            # --- JIRA EXPORT ---
            with st.expander("🛠️ View Jira-Format Ticket"):
                st.code(generate_jira_format(data), language="jira")
                st.info("Copy the text above and paste it directly into a Jira Ticket description!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# --- HISTORY SECTION ---
if st.session_state.history:
    st.divider()
    st.subheader("📜 Session History")
    
    # Iterate through history in reverse (newest first)
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
