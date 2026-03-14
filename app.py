"""
BridgeBuild AI - Agile Operating System
----------------------------------------------------
Author: Manan Patel
Version: 2.0.0 (Bulletproof URL Session Routing)
"""
import streamlit as st
from pm_dashboard import render_pm_dashboard
from admin_dashboard import render_admin_dashboard
from sales_dashboard import render_sales_dashboard
from design_dashboard import render_design_dashboard
from engineering_dashboard import render_engineering_dashboard
from supabase import create_client

# 1. PAGE CONFIG (Must absolute be first)
st.set_page_config(
    page_title="BridgeBuild AI",
    page_icon="Logo_bg_removed.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INITIALIZE SUPABASE
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

class MockUser:
    def __init__(self, uid):
        self.id = uid

# INITIALIZE SESSION STATE
if "history" not in st.session_state: st.session_state.history = []
if "logged_in" not in st.session_state: st.session_state.logged_in = False

def get_user_role(user_id):
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).execute()
        if response.data and len(response.data) > 0: return response.data[0]["role"]
        return "pm"
    except: return "pm"

# ==========================================
# THE BULLETPROOF URL LISTENER 🔗
# ==========================================
# If the user hits refresh, Streamlit instantly checks the URL for the session token!
if not st.session_state.logged_in and "session" in st.query_params:
    user_id = st.query_params["session"]
    st.session_state.user = MockUser(user_id)
    st.session_state.user_role = get_user_role(user_id)
    st.session_state.logged_in = True

def setup_custom_styling():
    """Supercharged Global CSS styles for the BridgeBuild Enterprise OS."""
    st.markdown("""
    <style>
        /* 1. WHITE-LABELING */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* 2. DUKE BLUE THEME VARIABLES */
        :root { 
            --primary-color: #012169; 
            --hover-color: #001547;
        }

        /* 3. PREMIUM BUTTON ANIMATIONS */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
            box-shadow: 0 4px 6px rgba(1, 33, 105, 0.1);
        }

        div.stButton > button[kind="primary"] {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px;
            font-weight: bold;
            padding: 0.5rem 1rem;
            box-shadow: 0 4px 6px rgba(1, 33, 105, 0.2);
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: var(--hover-color) !important;
            box-shadow: 0 6px 12px rgba(1, 33, 105, 0.3);
            transform: translateY(-2px);
        }

        /* 4. SAAS CARD STYLING */
        [data-testid="stExpander"] {
            border-radius: 10px !important;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            margin-bottom: 0.5rem;
            overflow: hidden;
        }
        
        /* 5. TYPOGRAPHY POLISH */
        [data-testid="stMetricValue"] {
            color: var(--primary-color) !important;
            font-weight: 800 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
# ==========================================
# THE MASTER ROUTER
# ==========================================
if not st.session_state.logged_in:
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
                if st.button("Log In", use_container_width=True, type="primary"):
                    try:
                        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        user_role = get_user_role(response.user.id)
                        
                        st.session_state.user = response.user
                        st.session_state.logged_in = True
                        st.session_state.user_role = user_role
                        
                        # THE MAGIC: Stamp the user ID directly into the URL!
                        st.query_params["session"] = response.user.id
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
            else:
                if st.button("Create Account", use_container_width=True, type="primary"):
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Account created! Please check your email to confirm.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")

else:
    # THE USER IS SECURELY LOGGED IN - DRAW THE APP
    setup_custom_styling()
    
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        with col_logo: st.image("Logo_bg_removed.png", width=40)
        with col_text:
            st.markdown("<h3 style='margin: 0; padding-top: 8px; font-size: 18px;'>BridgeBuild AI</h3>", unsafe_allow_html=True)
            
        st.caption(f"Role: {st.session_state.get('user_role', 'Unknown').upper()}")
        st.divider()

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
            except: pass

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.query_params.clear() # Wipes the URL clean!
            st.rerun()

    # RENDER SPECIFIC DASHBOARD 
    role = st.session_state.get("user_role", "pm") 
    if role == "sales": render_sales_dashboard(supabase)
    elif role == "pm": render_pm_dashboard(supabase)
    elif role == "design": render_design_dashboard(supabase)
    elif role == "admin": render_admin_dashboard(supabase)
    elif role == "engineering": render_engineering_dashboard(supabase)
    else: render_pm_dashboard(supabase)
