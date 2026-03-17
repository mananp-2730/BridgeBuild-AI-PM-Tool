"""
BridgeBuild AI - Agile Operating System
----------------------------------------------------
Author: Manan Patel
Version: 2.1.0 (Dynamic Dark Mode UI)
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
if not st.session_state.logged_in and "session" in st.query_params:
    user_id = st.query_params["session"]
    st.session_state.user = MockUser(user_id)
    st.session_state.user_role = get_user_role(user_id)
    st.session_state.logged_in = True

# ==========================================
# THE DYNAMIC THEME ENGINE 🎨
# ==========================================
def setup_custom_styling(is_dark=False):
    """Injects dynamic CSS based on the user's Dark Mode preference."""
    
    # Base White-Labeling & Button Physics (Applies to both modes)
    common_css = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"] {
            border: none !important;
            padding: 0.5rem 1rem;
        }
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
        }
    </style>
    """
    
    # The Light Theme (Duke Blue & Crisp White)
    light_css = """
    <style>
        :root { 
            --primary-color: #012169; 
            --hover-color: #001547;
            --bg-color: #F4F6F8;
            --text-color: #1E293B;
            --card-bg: #FFFFFF;
            --border-color: #e2e8f0;
        }
        
        div.stButton > button[kind="primary"] { background-color: var(--primary-color) !important; color: white !important; box-shadow: 0 4px 6px rgba(1, 33, 105, 0.2); }
        div.stButton > button[kind="primary"]:hover { background-color: var(--hover-color) !important; box-shadow: 0 6px 12px rgba(1, 33, 105, 0.3); }
        
        [data-testid="stSidebar"] { background-color: var(--card-bg) !important; border-right: 1px solid var(--border-color); }
        [data-testid="stExpander"] { background-color: var(--card-bg) !important; border-radius: 10px !important; border: 1px solid var(--border-color); box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        [data-testid="stMetricValue"] { color: var(--primary-color) !important; font-weight: 800 !important; }
    </style>
    """
    
    # The Dark Theme (Sleek Charcoal & Blue)
    dark_css = """
    <style>
        :root { 
            --primary-color: #3b82f6; 
            --hover-color: #60a5fa;
            --bg-color: #0e1117;
            --text-color: #f8fafc;
            --card-bg: #1e293b;
            --border-color: #334155;
        }
        
        /* Force Dark Backgrounds */
        .stApp { background-color: var(--bg-color) !important; color: var(--text-color) !important; }
        [data-testid="stSidebar"] { background-color: var(--card-bg) !important; border-right: 1px solid var(--border-color) !important; }
        [data-testid="stHeader"] { background-color: var(--bg-color) !important; }
        
        /* Text Overrides */
        h1, h2, h3, h4, h5, p, span, div, label { color: var(--text-color) !important; }
        
        /* Buttons & Cards */
        div.stButton > button[kind="primary"] { background-color: var(--primary-color) !important; color: white !important; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4); border: none !important; }
        div.stButton > button[kind="primary"]:hover { background-color: var(--hover-color) !important; }
        div.stButton > button[kind="secondary"] { background-color: var(--card-bg) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; }
        
        /* UI FLAW FIX: Download Buttons */
        div.stDownloadButton > button { background-color: var(--card-bg) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; }
        div.stDownloadButton > button:hover { border-color: var(--primary-color) !important; color: var(--primary-color) !important; }

        /* ========================================= */
        /* THE BOSS FIGHT: POPOVERS & ALERTS         */
        /* ========================================= */
        
        /* 1. The Trigger Button (The main Delete button) */
        div[data-testid="stPopover"] > div > button,
        div[data-testid="stPopoverTarget"] > button {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }
        div[data-testid="stPopover"] > div > button:hover,
        div[data-testid="stPopoverTarget"] > button:hover {
            border-color: var(--primary-color) !important;
            color: var(--primary-color) !important;
            background-color: var(--bg-color) !important;
        }
        
        /* 2. The Popover Menu Body (The floating container) */
        div[data-testid="stPopoverBody"] {
            background-color: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
        }
        
        /* 3. Strip the hidden white background from inner blocks */
        div[data-testid="stPopoverBody"] > div {
            background-color: transparent !important;
        }

        /* 4. Fix Alerts (The "Are you sure?" yellow box) */
        [data-testid="stAlert"] {
            background-color: rgba(30, 41, 59, 0.8) !important; /* Sleek, stealthy dark slate */
            border: 1px solid var(--border-color) !important;
        }
        [data-testid="stAlert"] * {
            color: var(--text-color) !important;
        }
        /* ========================================= */

        /* UI FLAW FIX: Expander Headers */
        [data-testid="stExpander"] { background-color: var(--card-bg) !important; border-radius: 10px !important; border: 1px solid var(--border-color) !important; }
        [data-testid="stExpander"] summary { background-color: var(--card-bg) !important; color: var(--text-color) !important; border-radius: 10px !important; }
        [data-testid="stExpander"] summary:hover { background-color: var(--bg-color) !important; }
        
        /* UI FLAW FIX: Inputs & Textareas */
        .stTextInput input, .stTextArea textarea, .stChatInputContainer { background-color: #0f172a !important; color: white !important; border: 1px solid var(--border-color) !important; }
        ::placeholder { color: #64748b !important; opacity: 1 !important; }
        
        /* File Uploader & Browse Button */
        [data-testid="stFileUploader"] > section { background-color: #0f172a !important; border: 1px dashed var(--border-color) !important; }
        [data-testid="stFileUploader"] * { color: var(--text-color) !important; }
        [data-testid="stFileUploader"] button { background-color: var(--card-bg) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; border-radius: 6px !important; font-weight: 600; }
        [data-testid="stFileUploader"] button:hover { border-color: var(--primary-color) !important; color: var(--primary-color) !important; background-color: var(--bg-color) !important; }
        
        /* Selectbox */
        div[data-baseweb="select"] > div { background-color: #0f172a !important; color: white !important; border-color: var(--border-color) !important; }
        ul[data-baseweb="menu"] { background-color: #0f172a !important; color: white !important; }
        
        [data-testid="stMetricValue"] { color: var(--primary-color) !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    </style>
    """
    
    if is_dark:
        st.markdown(common_css + dark_css, unsafe_allow_html=True)
    else:
        st.markdown(common_css + light_css, unsafe_allow_html=True)
        
# ==========================================
# THE MASTER ROUTER
# ==========================================
if not st.session_state.logged_in:
    # Render default light CSS for the login page
    setup_custom_styling(is_dark=False)
    
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
    
    # Grab the user's settings so we know if they want Dark Mode!
    if "user_prefs" not in st.session_state:
        try:
            res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
            st.session_state.user_prefs = res.data[0] if res.data else {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)", "dark_mode": False}
        except:
            st.session_state.user_prefs = {"currency": "USD ($)", "rate_standard": "US Agency ($150/hr)", "ai_model": "Gemini 1.5 Flash (Fast)", "dark_mode": False}

    # Extract current dark mode status from DB/Session
    is_dark_mode = st.session_state.user_prefs.get("dark_mode", False)
    
    # Fire the theme engine!
    setup_custom_styling(is_dark=is_dark_mode)
    
    with st.sidebar:
        col_logo, col_text = st.columns([0.2, 0.8])
        with col_logo: st.image("Logo_bg_removed.png", width=40)
        with col_text:
            st.markdown("<h3 style='margin: 0; padding-top: 8px; font-size: 18px;'>BridgeBuild AI</h3>", unsafe_allow_html=True)
            
        st.caption(f"Role: {st.session_state.get('user_role', 'Unknown').upper()}")
        st.divider()

        st.markdown("#### Global Settings")
        
        # --- THE DARK MODE TOGGLE ---
        new_dark = st.toggle("🌙 Night Mode", value=is_dark_mode)

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
            new_prefs = {
                "currency": new_curr, 
                "rate_standard": new_rate, 
                "ai_model": new_model,
                "dark_mode": new_dark # Save the theme state to DB!
            }
            try:
                supabase.table("profiles").update(new_prefs).eq("id", st.session_state.user.id).execute()
                st.session_state.user_prefs.update(new_prefs)
                st.success("Global Settings Saved!")
                st.rerun() # Instantly repaints the screen with the new theme!
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
