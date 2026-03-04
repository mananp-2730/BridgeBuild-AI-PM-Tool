import streamlit as st
import json
import os
import tempfile
from google import genai
from google.genai import types
from prompts import get_sales_prompt
from utils import clean_json_output, convert_currency

def render_sales_dashboard():
    with st.sidebar:
        st.markdown("### Sales Portal")
        st.write(f"Logged in as: {st.session_state.get('user_role', 'Unknown').upper()}")
        
        st.divider()
        if st.button("Logout", key="sales_logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("BridgeBuild AI - Sales Intake")
    st.markdown("### Quickly validate requirements and get estimated timelines.")

    uploaded_file = st.file_uploader("Upload Client Audio (.mp3, .wav)", type=["mp3", "wav", "m4a"])
    
    # Render audio player if they upload a file
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['mp3', 'wav', 'm4a']:
            st.audio(uploaded_file)
            
    sales_input = st.text_area("Or Paste Notes:", height=150, placeholder="Example: Client needs a basic e-commerce site with Stripe integration.")

    api_key = st.secrets.get("GOOGLE_API_KEY")
    rate_type = st.session_state.get("user_prefs", {}).get("rate_standard", "US Agency ($150/hr)")
    currency = st.session_state.get("user_prefs", {}).get("currency", "USD ($)")
    model_choice = st.session_state.get("user_prefs", {}).get("ai_model", "Gemini 1.5 Flash (Fast)")

    if st.button("Analyze Request", type="primary"):
        if not api_key:
            st.error("System Error: AI Engine is currently offline. Please contact support.")
        elif not sales_input and not uploaded_file:
            st.warning("Please enter text or upload a file to proceed.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                SALES_PROMPT = get_sales_prompt(rate_type)

                with st.spinner("Analyzing feasibility & estimating budget..."):
                    model_id = "gemini-2.5-flash" if "Flash" in model_choice else "gemini-2.5-pro"
                    prompt_contents = []
                    
                    if uploaded_file:
                        st.toast("Processing file...", icon="⏳")
                        file_ext = f".{uploaded_file.name.split('.')[-1]}"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        gemini_file = client.files.upload(file=tmp_path)
                        prompt_contents.append(gemini_file)
                        os.remove(tmp_path)
                    
                    text_instruction = sales_input if sales_input else "Analyze this client request."
                    prompt_contents.append(text_instruction)
                    
                    response = client.models.generate_content(
                        model=model_id, 
                        config=types.GenerateContentConfig(
                            system_instruction=SALES_PROMPT,
                            temperature=0.0,
                            response_mime_type="application/json"
                        ),
                        contents=prompt_contents
                    )
                    
                    if uploaded_file:
                        client.files.delete(name=gemini_file.name)
                    
                    cleaned_text = clean_json_output(response.text)
                    data = json.loads(cleaned_text)

                st.write("")
                score = data.get("feasibility_score", "Yellow")
                if "Green" in score:
                    st.success(f"### 🟢 Feasibility: GREEN\n{data.get('feasibility_reason')}")
                elif "Red" in score:
                    st.error(f"### 🔴 Feasibility: RED\n**Warning:** {data.get('feasibility_reason')}")
                else:
                    st.warning(f"### 🟡 Feasibility: YELLOW\n{data.get('feasibility_reason')}")
                    
                st.markdown(f"**Project Summary:** {data.get('project_summary')}")
                st.divider()

                raw_cost = data.get("budget_estimate_usd", "0-0")
                low_end = raw_cost.split("-")[0] if "-" in raw_cost else raw_cost
                high_end = raw_cost.split("-")[1] if "-" in raw_cost else raw_cost
                fmt_low = convert_currency(low_end, currency)
                fmt_high = convert_currency(high_end, currency)
                
                col1, col2 = st.columns(2)
                with col1: st.metric("Estimated MVP Timeline", data.get("estimated_timeline"))
                with col2: st.metric("Estimated MVP Budget", f"{fmt_low} - {fmt_high}")
                    
                st.divider()
                
                col_q, col_r = st.columns(2)
                with col_q:
                    st.subheader("The 'Ask' List")
                    st.caption("Critical missing info to ask the client:")
                    for q in data.get("client_questions", []): st.info(f"{q}")
                        
                with col_r:
                    st.subheader("Deal Breakers")
                    st.caption("Major risks to watch out for:")
                    for r in data.get("deal_breakers", []): st.error(f"{r}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
