"""
BridgeBuild AI - Agile Operating System
----------------------------------------------------
Author: Manan Patel
Version: 1.4.0 (Modular Architecture)
"""
import streamlit as st

# 1. PAGE CONFIG (Must absolute be first)
st.set_page_config(
    page_title="BridgeBuild AI",
    page_icon="Logo_bg_removed.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. IMPORT OUR NEW DASHBOARDS
from pm_dashboard import render_pm_dashboard
from admin_dashboard import render_admin_dashboard
from sales_dashboard import render_sales_dashboard
from design_dashboard import render_design_dashboard
from supabase import create_client

# 3. INITIALIZE SUPABASE
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# INITIALIZE SESSION STATE
if "history" not in st.session_state: st.session_state.history = []
if "logged_in" not in st.session_state: st.session_state.logged_in = False

def get_user_role(user_id):
    """Fetches the user's department role from Supabase."""
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["role"]
        return "pm"
    except Exception as e:
        print(f"Error fetching role: {e}")
        return "pm"

def setup_custom_styling():
    """Global CSS styles for the app."""
    st.markdown("""
    <style>
        :root { --primary-color: #012169; }
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { background-color: #012169 !important; border-color: #012169 !important; }
        div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child > div { background-color: white !important; }
        div[data-baseweb="slider"] div[role="slider"] { background-color: #012169 !important; box-shadow: none !important; }
        div[data-baseweb="slider"] div[data-testid="stTickBar"] > div { background-color: #012169 !important; }
        div[data-testid="stMarkdownContainer"] p code { color: #012169 !important; }
        div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: #012169 !important; border-color: #012169 !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; margin-top: -50px !important; }
        div.stButton > button:first-child { background-color: #012169; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; padding: 12px 24px; }
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div { color: var(--text-color) !important; }
        div.stButton > button:first-child:hover { background-color: #001547; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

# 4. LOGIN PAGE
def login_page():
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            .block-container { padding-top: 3rem !important; padding-bottom: 0rem !important; }
            div.stButton > button[kind="primary"] { background-color: #012169 !important; border: none !important; }
            div.stButton > button[kind="primary"]:hover { background-color: #001547 !important; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            c_img1, c_img2, c_img3 = st.columns([1, 1, 0.6])
            with c_img2: st.image("Logo_bg_removed.png", width=80)
            
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
                        st.session_state.user_role = get_user_role(response.user.id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
            else:
                if st.button("Create Account", use_container_width=True, type="primary", key="signup_btn"):
                    try:
                        response = supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Account created! Please check your email to confirm.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")

def render_global_sidebar(supabase):
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        with col_logo: st.image("Logo_bg_removed.png", width=40)
        with col_text:
            st.markdown("<h3 style='margin: 0; padding-top: 8px; font-size: 18px;'>BridgeBuild AI</h3>", unsafe_allow_html=True)
            
        st.caption(f"Role: {st.session_state.get('user_role', 'Unknown').upper()}")
        st.divider()

        # Fetch Preferences
        if "user_prefs" not in st.session_state:
            try:
                res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
                st.session_state.user_prefs = res.data[0] if res.data else {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)"}
            except:
                st.session_state.user_prefs = {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)"}

        st.markdown("#### Global Settings")
        curr_opts = ["USD ($)", "INR (₹)"]
        rate_opts = ["US Agency ($150/hr)", "India Agency ($40/hr)", "Freelancer ($20/hr)"]
        model_opts = ["Gemini 1.5 Flash (Fast)", "Gemini 1.5 Pro (High Reasoning)"]

        # Safely get indexes
        curr_idx = curr_opts.index(st.session_state.user_prefs.get("currency", "USD ($)")) if st.session_state.user_prefs.get("currency") in curr_opts else 0
        rate_idx = rate_opts.index(st.session_state.user_prefs.get("rate_standard", "US Agency ($150/hr)")) if st.session_state.user_prefs.get("rate_standard") in rate_opts else 0
        model_idx = model_opts.index(st.session_state.user_prefs.get("ai_model", "Gemini 1.5 Flash (Fast)")) if st.session_state.user_prefs.get("ai_model") in model_opts else 0

        new_curr = st.radio("Display Currency:", curr_opts, index=curr_idx, horizontal=True)
        new_rate = st.selectbox("Rate Standard:", rate_opts, index=rate_idx)
        new_model = st.radio("AI Engine:", model_opts, index=model_idx)

        if st.button("Save Settings", use_container_width=True):
            new_prefs = {"currency": new_curr, "rate_standard": new_rate, "ai_model": new_model}
            try:
                supabase.table("profiles").update(new_prefs).eq("id", st.session_state.user.id).execute()
                st.session_state.user_prefs.update(new_prefs)
                st.success("Global Settings Saved!")
                st.rerun()
            except Exception as e:
                st.error("Failed to save.")

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
# 5. THE ROUTER (Traffic Cop)
if st.session_state.logged_in:
    setup_custom_styling() # Load styles once!
    role = st.session_state.get("user_role", "pm") 
    
    if role == "sales":
        render_sales_dashboard(supabase)
    elif role == "pm":
        render_pm_dashboard(supabase) # PM needs database access
    elif role == "design":
        render_design_dashboard(supabase)
    elif role == "admin":
        render_admin_dashboard(supabase)
    else:
        st.warning(f"Dashboard for role '{role}' is currently under development. Loading PM Dashboard.")
        render_pm_dashboard(supabase)
else:
    login_page()
