import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
import PIL.Image

# Load environment variables for local development
load_dotenv()

# Configuration
st.set_page_config(page_title="LUCID Voting", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Home"
if 'voter_id' not in st.session_state:
    st.session_state.voter_id = None
if 'show_login_modal' not in st.session_state:
    st.session_state.show_login_modal = False
if 'login_tab' not in st.session_state:
    st.session_state.login_tab = "login"
if 'show_login_dialog' not in st.session_state:
    st.session_state.show_login_dialog = False

# Custom CSS - Federal Government Website Style
st.markdown("""
    <style>
        /* Hide Streamlit default header, menu, and footer */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Remove default padding/margin - minimal spacing */
        .stApp {
            margin-top: 0;
            padding-top: 0;
            padding-left: 0;
            padding-right: 0;
            font-family: "Source Sans Pro", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }
        
        /* Remove Streamlit's default block container padding */
        .block-container {
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
            margin-top: 0 !important;
        }
        
        /* Remove any default spacing from Streamlit elements */
        .stApp > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Ensure top banner starts at the very top */
        #root > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Ensure main content extends to edges */
        .main-container {
            width: 100%;
            padding: 0;
            margin: 0;
        }
        
        /* Top banner - 36px height for Login link */
        .top-banner {
            background-color: #1b1b1b;
            color: #ffffff;
            height: 36px;
            padding: 0 2rem;
            border-bottom: 4px solid #005ea2;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        
        .top-banner-content {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 1rem;
            height: 100%;
        }
        
        .login-link {
            color: #005ea2 !important;
            text-decoration: underline !important;
            cursor: pointer !important;
            font-size: 0.875rem !important;
            background: none !important;
            border: none !important;
            padding: 0 !important;
            font-weight: 600 !important;
        }
        
        .login-link:hover {
            color: #1a4480 !important;
            text-decoration: none !important;
        }
        
        /* Modal Dialog Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            overflow: auto;
        }
        
        .modal-content {
            background-color: #ffffff;
            margin: 5% auto;
            padding: 2rem;
            border: 1px solid #c9c9c9;
            border-radius: 8px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #005ea2;
        }
        
        .modal-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #005ea2;
            margin: 0;
        }
        
        .close {
            color: #1b1b1b;
            font-size: 2rem;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
        }
        
        .close:hover {
            color: #005ea2;
        }
        
        .modal-tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid #c9c9c9;
        }
        
        .modal-tab {
            padding: 0.75rem 1.5rem;
            background: none;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            color: #1b1b1b;
        }
        
        .modal-tab.active {
            color: #005ea2;
            border-bottom-color: #005ea2;
        }
        
        .modal-tab:hover {
            color: #005ea2;
        }
        
        .modal-form {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .form-label {
            font-weight: 600;
            color: #1b1b1b;
            font-size: 0.9375rem;
        }
        
        .form-input {
            padding: 0.75rem;
            border: 1px solid #c9c9c9;
            border-radius: 4px;
            font-size: 1rem;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #005ea2;
            box-shadow: 0 0 0 2px rgba(0, 94, 162, 0.2);
        }
        
        .modal-button {
            background-color: #005ea2;
            color: #ffffff;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 0.5rem;
        }
        
        .modal-button:hover {
            background-color: #1a4480;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Main Header */
        .main-header {
            background-color: #E9ECEF;
            border-bottom: 0.25rem solid #005ea2;
            height: 46px;
            padding: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
        }
        
        .header-container {
            width: 100%;
            padding: 0 2rem;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            height: 100%;
        }
        
        .header-logo {
            font-size: 1.625rem;
            font-weight: 700;
            color: #005ea2;
            text-decoration: none !important;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            line-height: 1;
        }
        
        .header-logo:hover {
            color: #1a4480;
            text-decoration: none !important;
        }
        
        .header-logo:visited {
            text-decoration: none !important;
        }
        
        .header-logo:active {
            text-decoration: none !important;
        }
        
        .status-badge {
            background-color: #333333 !important;
            color: #ffffff !important;
            padding: 0.15rem 0.5rem !important;
            border-radius: 4px !important;
            font-size: 0.7rem !important;
            font-weight: 600 !important;
            border: 1px solid #444444 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }
        
        .status-badge.verified {
            background-color: #2e8540 !important;
            color: #ffffff !important;
            border-color: #2e8540 !important;
        }
        
        /* Main Content Area */
        .main-content {
            width: 100%;
            margin: 0;
            padding: 2rem;
            background-color: #ffffff;
            min-height: 60vh;
        }
        
        /* Page Title */
        .page-title {
            font-size: 2rem;
            font-weight: 700;
            color: #1b1b1b;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #005ea2;
        }
        
        /* Bill Cards */
        .bill-card {
            background-color: #ffffff;
            border: 1px solid #c9c9c9;
            border-left: 4px solid #005ea2;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .bill-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .bill-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #005ea2;
            margin-top: 0;
            margin-bottom: 1rem;
        }
        
        .bill-summary {
            color: #1b1b1b;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        
        .pros-cons-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .pros-section, .cons-section {
            padding: 1rem;
            border-radius: 4px;
        }
        
        .pros-section {
            background-color: #e7f4e4;
            border-left: 4px solid #2e8540;
        }
        
        .cons-section {
            background-color: #fce8e6;
            border-left: 4px solid #d54309;
        }
        
        .section-title {
            font-size: 1.125rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 0.75rem;
        }
        
        .pros-title {
            color: #2e8540;
        }
        
        .cons-title {
            color: #d54309;
        }
        
        .pros-list, .cons-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .pros-list li, .cons-list li {
            padding: 0.5rem 0;
            color: #1b1b1b;
        }
        
        /* Button Styling */
        .stButton > button {
            background-color: #005ea2;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        
        .stButton > button:hover {
            background-color: #1a4480;
        }
        
        /* Info Boxes */
        .info-box {
            background-color: #e7f2f5;
            border-left: 4px solid #005ea2;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .warning-box {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Footer */
        .footer {
            background-color: #1b1b1b;
            color: #ffffff;
            padding: 2rem;
            margin-top: 3rem;
            border-top: 4px solid #005ea2;
        }
        
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
            font-size: 0.875rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .pros-cons-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Helper to get configuration from st.secrets or environment variables
def get_config(key, default=None):
    try:
        return st.secrets[key]
    except (KeyError, AttributeError, FileNotFoundError):
        return os.getenv(key, default)

# Authentication Dialog
@st.dialog("Account Access")
def auth_dialog():
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        st.markdown("### Welcome Back")
        email = st.text_input("Email", key="login_email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit", type="primary", key="login_submit_btn", use_container_width=True):
                if email and password:
                    try:
                        # Authenticate with Supabase
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res.user:
                            # Fetch the Voter ID from the profile table
                            profile_res = supabase.table("profiles").select("voter_id").eq("id", res.user.id).single().execute()
                            st.session_state.voter_id = profile_res.data.get("voter_id")
                            st.success("Login Successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
                else:
                    st.error("Please fill in all fields.")
        
        with col2:
            st.markdown('<div style="text-align: right; padding-top: 10px;"><a href="#" style="color: #005ea2; font-size: 0.85rem;">Forgot Password?</a></div>', unsafe_allow_html=True)

    with tab_register:
        st.markdown("### Create Account")
        reg_email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
        reg_password = st.text_input("Password", type="password", key="reg_pass", placeholder="Create a password (min 8 chars)")
        
        if st.button("Register", type="primary", key="register_submit_btn", use_container_width=True):
            if reg_email and len(reg_password) >= 8:
                try:
                    # Sign up with Supabase
                    res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                    if res.user:
                        st.success("Account created! Please check your email for confirmation (if enabled) or try logging in.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
            elif len(reg_password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                st.error("Please fill in all fields.")

# Initialize API Keys
gemini_key = get_config("GEMINI_API_KEY") or get_config("GOOGLE_API_KEY")
supabase_url = get_config("SUPABASE_URL")
supabase_key = get_config("SUPABASE_KEY")

# Initialize Gemini
model = None
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    st.error("Missing GEMINI_API_KEY. Please set it in Streamlit Secrets or a .env file.")

# Initialize Supabase
supabase: Client = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
else:
    st.error("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets or a .env file.")

# Top Banner and Main Header
voter_status = f"Verified: {st.session_state.voter_id}" if st.session_state.voter_id else "Guest"
status_class = "verified" if st.session_state.voter_id else ""

st.markdown(f"""
    <div class="top-banner">
        <div class="top-banner-content">
            <a href="?auth=true" target="_self" class="login-link">Register/Login</a>
            <span class="status-badge {status_class}">{voter_status}</span>
        </div>
    </div>
    <div class="main-header">
        <div class="header-container">
            <a href="/" target="_self" class="header-logo">⚖️ LUCID Voting</a>
        </div>
    </div>
""", unsafe_allow_html=True)

# Check if we should show the dialog
if st.query_params.get("auth") == "true":
    # Clear query params to prevent dialog from reopening on manual refresh
    st.query_params.clear()
    auth_dialog()

# Main Content Area
st.markdown('<div class="main-content">', unsafe_allow_html=True)

if st.session_state.current_view == "Home":
    st.markdown('<h1 class="page-title">Latest Legislation</h1>', unsafe_allow_html=True)
    
    if supabase:
        try:
            # Query last 5 bills
            response = supabase.table("bills").select("*").order("created_at", desc=True).limit(5).execute()
            bills = response.data
            
            if not bills:
                st.info("No bills found in the database yet.")
            else:
                for bill in bills:
                    title = bill.get('title', 'Untitled Bill')
                    summary = bill.get('simple_summary', 'No summary available.')
                    
                    pros = bill.get('pros', [])
                    if not isinstance(pros, list):
                        pros = [pros] if pros else []
                    
                    cons = bill.get('cons', [])
                    if not isinstance(cons, list):
                        cons = [cons] if cons else []
                    
                    pros_html = ""
                    for pro in pros:
                        pros_html += f"<li>{pro}</li>"
                            
                    cons_html = ""
                    for con in cons:
                        cons_html += f"<li>{con}</li>"
                    
                    card_html = f"""
                    <div class="bill-card">
                        <h2 class="bill-title">{title}</h2>
                        <div class="bill-summary">
                            <strong>Summary:</strong> {summary}
                        </div>
                        <div class="pros-cons-container">
                            <div class="pros-section">
                                <h3 class="section-title pros-title">Pros</h3>
                                <ul class="pros-list">
                                    {pros_html if pros_html else '<li>No pros listed.</li>'}
                                </ul>
                            </div>
                            <div class="cons-section">
                                <h3 class="section-title cons-title">Cons</h3>
                                <ul class="cons-list">
                                    {cons_html if cons_html else '<li>No cons listed.</li>'}
                                </ul>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Error fetching bills: {e}")
    else:
        st.warning("Supabase not configured.")

elif st.session_state.current_view == "Vote":
    st.markdown('<h1 class="page-title">My Vote</h1>', unsafe_allow_html=True)
    if st.session_state.voter_id:
        st.info(f"You are logged in as Verified Voter: {st.session_state.voter_id}")
        st.write("Voting functionality coming soon!")
    else:
        st.warning("Please login/verify first to access voting features.")
        if st.button("Go to Login"):
            st.session_state.current_view = "Login"
            st.rerun()

elif st.session_state.current_view == "Login":
    st.markdown('<h1 class="page-title">Biometric Verification</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>Secure Identity Verification</strong><br>
        Please use your camera to verify your identity. This process uses advanced biometric verification 
        to ensure secure access to voting features.
    </div>
    """, unsafe_allow_html=True)
    
    # Camera input
    camera_image = st.camera_input("Take a photo for verification")
    
    if camera_image:
        if not model:
            st.error("Gemini API not configured. Cannot verify identity.")
        else:
            # Convert camera image to PIL Image
            img = PIL.Image.open(camera_image)
            
            # Verify with Gemini Vision
            verify_button = st.button("Verify Identity", type="primary")
            
            if verify_button:
                with st.spinner("Verifying identity with Gemini Vision..."):
                    try:
                        # Use Gemini Vision to check if it's a real human
                        prompt = "Is this a real human? Respond with only 'YES' or 'NO'."
                        response = model.generate_content([prompt, img])
                        
                        result = response.text.strip().upper()
                        
                        if "YES" in result:
                            # Generate a voter ID (in production, this would be more sophisticated)
                            import hashlib
                            import time
                            voter_id = hashlib.md5(f"{time.time()}{camera_image.getvalue()}".encode()).hexdigest()[:8].upper()
                            
                            st.session_state.voter_id = voter_id
                            st.success(f"✅ Verification successful! Your Voter ID: {voter_id}")
                            st.balloons()
                            
                            # Switch back to Home view
                            st.session_state.current_view = "Home"
                            st.rerun()
                        else:
                            st.error("❌ Verification failed. Please ensure you are a real human and try again.")
                    except Exception as e:
                        st.error(f"Error during verification: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <p><strong>LUCID</strong> - Legislative Understanding Creates Informed Decisions</p>
            <p style="margin-top: 1rem;">
                <a href="#" style="color: #ffffff; margin: 0 1rem;">Accessibility</a>
                <a href="#" style="color: #ffffff; margin: 0 1rem;">Privacy Policy</a>
                <a href="#" style="color: #ffffff; margin: 0 1rem;">Security</a>
                <a href="#" style="color: #ffffff; margin: 0 1rem;">Contact Us</a>
            </p>
            <p style="margin-top: 1rem; font-size: 0.75rem;">
                An official website of the U.S. Government
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Admin section (hidden, but accessible via URL parameter)
if st.query_params.get("admin") == "true":
    st.markdown("---")
    st.markdown("### Admin: Add New Bill")
    
    bill_text = st.text_area("Paste Bill Text", height=300)
    analyze_button = st.button("Analyze & Save")
    
    if analyze_button:
        if not bill_text:
            st.warning("Please paste some bill text first.")
        elif not model or not supabase:
            st.error("API keys or Supabase connection missing.")
        else:
            with st.spinner("Analyzing legislation with Gemini..."):
                try:
                    prompt = (
                        "Summarize this legislation. Return ONLY a valid JSON object with the following keys: "
                        "'title', 'simple_summary' (5th grade level), 'pros' (list of 3), 'cons' (list of 3). "
                        "Do not include any markdown formatting like ```json or any other text.\n\n"
                        f"Legislation Text:\n{bill_text}"
                    )
                    
                    response = model.generate_content(prompt)
                    
                    # Clean the response to ensure it's valid JSON
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text.replace("```json", "", 1).replace("```", "", 1).strip()
                    elif raw_text.startswith("```"):
                        raw_text = raw_text.replace("```", "", 2).strip()
                    
                    analysis = json.loads(raw_text)
                    
                    # Display preview
                    st.success("Analysis Complete!")
                    st.json(analysis)
                    
                    # Save to Supabase
                    with st.spinner("Saving to database..."):
                        save_response = supabase.table("bills").insert(analysis).execute()
                        if save_response.data:
                            st.balloons()
                            st.success(f"Successfully saved: {analysis['title']}")
                        else:
                            st.error("Failed to save to Supabase.")
                            
                except json.JSONDecodeError:
                    st.error("Gemini returned invalid JSON. Please try again.")
                    st.text(response.text)  # For debugging
                except Exception as e:
                    st.error(f"An error occurred: {e}")
