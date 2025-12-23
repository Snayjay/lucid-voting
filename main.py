import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
import PIL.Image
import time
import io
import hashlib
import pandas as pd

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
if 'pending_voter_id' not in st.session_state:
    st.session_state.pending_voter_id = None
if 'reg_step' not in st.session_state:
    st.session_state.reg_step = 1
if 'reg_data' not in st.session_state:
    st.session_state.reg_data = {}

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

        /* Anchor-based targeting for the federal header row */
        div:has(> #header-anchor) + div[data-testid="stHorizontalBlock"] {
            background-color: #1b1b1b !important;
            border-bottom: 4px solid #005ea2 !important;
            padding: 0.5rem 2rem !important;
            z-index: 1000 !important;
            position: fixed !important;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
        }
        
        /* Content Buffers */
        .logo-buffer {
            margin-left: 20px !important;
        }
        
        .title-buffer {
            padding-left: 25px !important;
            margin-left: 0 !important;
        }
        
        /* Iris Scanner Styles - Apply zoom to both live video and the captured result image */
        div[data-testid="stCameraInput"] video, 
        div[data-testid="stCameraInput"] img {
            transform: scale(1.5) !important;
            transform-origin: center !important;
        }
        
        .scanner-guide {
            border: 2px dashed #B7986C;
            border-radius: 50%;
            width: 250px;
            height: 250px;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #B7986C;
            text-align: center;
            font-weight: 600;
            background-color: rgba(183, 152, 108, 0.1);
        }
        
        .scanning-text {
            color: #005ea2;
            font-weight: 700;
            font-family: monospace;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-align: center;
            margin-top: 10px;
        }

        /* Top banner fallback - can be used as a spacer if needed */
        .top-banner {
            background-color: transparent;
            height: 0;
            margin: 0;
            padding: 0;
        }
        
        .top-banner-content {
            display: none;
        }
        
        .login-link {
            display: none;
        }

        /* Disguised button for header */
        div[data-testid="stButton"] > button {
            background-color: transparent !important;
            border: none !important;
            color: #F6F6F6 !important; /* Off-White for dark background */
            text-decoration: underline !important;
            font-size: 0.875rem !important;
            font-weight: 700 !important;
            padding: 0 !important;
            margin: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            box-shadow: none !important;
            line-height: 1.2 !important;
            width: auto !important;
        }

        div[data-testid="stButton"] > button:hover {
            color: #B7986C !important; /* Gold Accent on hover */
            text-decoration: none !important;
            background-color: transparent !important;
        }

        div[data-testid="stButton"] > button:active {
            background-color: transparent !important;
        }

        /* Banner adjustment for columns - Cleanup of unused class */
        .top-banner-unused {
            display: none;
        }
        
        /* Logo styling in header */
        .header-logo-text {
            color: #F6F6F6 !important; /* Off-White for dark background */
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            padding: 0;
            text-decoration: none !important;
        }
        
        .header-bg {
            background-color: #E9ECEF;
            border-bottom: 0.25rem solid #005ea2;
            height: 46px;
            padding: 0 2rem;
            display: flex;
            align-items: center;
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
        
        /* Main Content Anchor Targeting */
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] {
            background-color: #ffffff !important;
            padding: 2rem 5% !important;
            min-height: calc(100vh - 150px) !important;
            color: #1b1b1b !important;
            margin-top: 70px !important;
            margin-bottom: 80px !important;
            position: relative !important;
            z-index: 1 !important;
            overflow-y: auto !important;
        }

        /* Ensure text inside the white area is visible (dark text) */
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] h1,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] h2,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] h3,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] p,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] li,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] .stMarkdown,
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] .stExpander p {
            color: #1b1b1b !important;
        }

        /* Adjust expanders inside the white area */
        div:has(> #main-anchor) + div[data-testid="stVerticalBlock"] .stExpander {
            background-color: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
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
            background-color: #1b1b1b !important;
            color: #ffffff !important;
            padding: 1rem 2rem !important;
            border-top: 4px solid #005ea2 !important;
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 1000 !important;
            height: 80px;
        }
        
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
            font-size: 0.875rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .logo-buffer {
                margin-left: 10px !important;
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

# Helper function to determine the current redirect URL for Supabase Auth
def get_redirect_url():
    # Logic: Default to the Live URL
    url = "https://lucid-voting.streamlit.app"
    
    # If we find a local .env file (which implies we are on your laptop), switch to localhost
    if os.path.exists(".env"): 
        url = "http://localhost:8501"
        
    return url

# Biometric Verification Helper
def verify_biometric_match(reference_bytes, current_bytes):
    if not model:
        return False
    
    try:
        ref_img = PIL.Image.open(io.BytesIO(reference_bytes))
        live_img = PIL.Image.open(io.BytesIO(current_bytes))
        
        prompt = """You are a biometric security officer. You have two images. Image A is the Reference. Image B is the Live Scan.
        Task 1: LIVENESS. Does Image B appear to be a live capture (not a photo of a screen)?
        Task 2: MATCH. Do the facial features in Image B match Image A?
        Return JSON: {"liveness": true, "match": true, "confidence": "high"}"""
        
        response = model.generate_content([prompt, ref_img, live_img])
        
        # Parse JSON from response
        raw_response = response.text.strip()
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].strip()
            
        # Robustly handle single quotes before parsing
        raw_response = raw_response.replace("'", '"')
            
        result_json = json.loads(raw_response)
        return result_json.get('liveness', False) and result_json.get('match', False)
    except Exception as e:
        st.error(f"Verification Error: {e}")
        return False

# Biometric Storage Helpers
def upload_biometric(voter_id, image_data):
    try:
        # If image_data is PIL Image, convert to bytes
        if hasattr(image_data, 'save'):
            img_byte_arr = io.BytesIO()
            image_data.save(img_byte_arr, format='JPEG')
            image_data = img_byte_arr.getvalue()
            
        supabase.storage.from_("biometrics").upload(
            path=f"{voter_id}_ref.jpg",
            file=image_data,
            file_options={"content-type": "image/jpeg"}
        )
        return True
    except Exception as e:
        st.error(f"Storage Upload Failed: {e}")
        return False

def get_biometric_ref(voter_id):
    try:
        return supabase.storage.from_("biometrics").download(f"{voter_id}_ref.jpg")
    except Exception as e:
        # Don't show error here as we handle missing IDs in the UI
        return None

# Biometric Identity Portal
@st.dialog("Biometric Identity Portal")
def login_dialog():
    if 'reg_step' not in st.session_state:
        st.session_state.reg_step = 1
    
    mode = st.radio("Choose Action", ["New Voter Registration", "Verify Identity"], horizontal=True, key="portal_mode")
    
    st.markdown("---")
    
    if mode == "Verify Identity":
        claimed_passcode = st.text_input("Enter your 10-digit Passcode", type="password", placeholder="Your secret code")
        camera_image = st.camera_input("Biometric Scan")
        
        if camera_image:
            if st.button("Verify Match", type="primary", use_container_width=True):
                with st.spinner("Biometric Matching..."):
                    time.sleep(1.5)
                    try:
                        # Convert camera image to bytes
                        img = PIL.Image.open(camera_image)
                        
                        # Apply Digital Zoom (1.5x) to match the CSS preview
                        width, height = img.size
                        new_width = width / 1.5
                        new_height = height / 1.5
                        img = img.crop(((width - new_width) / 2, (height - new_height) / 2, (width + new_width) / 2, (height + new_height) / 2))
                        
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        current_bytes = img_byte_arr.getvalue()

                        # Lookup Voter ID by hashed passcode
                        hashed_claimed = hashlib.sha256(claimed_passcode.encode()).hexdigest()
                        profile_res = supabase.table("profiles").select("voter_id").eq("passcode_hash", hashed_claimed).execute()
                        
                        if profile_res.data:
                            voter_id = profile_res.data[0]['voter_id']
                            ref_bytes = get_biometric_ref(voter_id)
                            
                            if ref_bytes:
                                if verify_biometric_match(ref_bytes, current_bytes):
                                    st.success("✅ Identity Verified. Welcome back.")
                                    st.session_state.voter_id = voter_id
                                    st.session_state.show_login_dialog = False
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Biometric Mismatch: Identity could not be confirmed.")
                            else:
                                st.error("❌ System Error: Biometric record not found.")
                        else:
                            st.error("❌ Invalid Passcode.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    else:
        # REGISTRATION WIZARD
        steps = ["Passcode", "ID Front", "ID Back", "Live Scan"]
        st.write(f"Step {st.session_state.reg_step} of 4: {steps[st.session_state.reg_step-1]}")
        
        if st.session_state.reg_step == 1:
            reg_passcode = st.text_input("Create a 10-digit Passcode", type="password", placeholder="Minimum 10 characters")
            verify_passcode = st.text_input("Verify Passcode", type="password", placeholder="Re-enter your passcode")
            
            # Real-time verification display
            if verify_passcode:
                if reg_passcode == verify_passcode and len(reg_passcode) >= 10:
                    st.success("✅ Passcodes match and meet length requirement.")
                elif reg_passcode == verify_passcode:
                    st.warning("⚠️ Passcodes match but must be at least 10 characters.")
                else:
                    st.error("❌ Passcodes do not match.")

            if st.button("Next: Scan ID Front", use_container_width=True):
                if len(reg_passcode) < 10:
                    st.error("Passcode must be at least 10 characters.")
                elif not reg_passcode.isalnum():
                    st.error("Passcode must be alphanumeric (letters and numbers only).")
                elif reg_passcode != verify_passcode:
                    st.error("Passcodes do not match. Please try again.")
                else:
                    st.session_state.reg_data['passcode'] = reg_passcode
                    st.session_state.reg_step = 2
                    st.rerun()

        elif st.session_state.reg_step == 2:
            st.info("📷 Capture the FRONT of your Government ID. Ensure all text is readable.")
            id_front = st.camera_input("Scan ID Front")
            if id_front:
                if st.button("Process ID Front", type="primary", use_container_width=True):
                    with st.spinner("Extracting ID Information..."):
                        try:
                            img = PIL.Image.open(id_front)
                            prompt = 'Extract Name, Address, and Date of Birth from this ID. Also, is this a valid ID? Respond ONLY with JSON: {"name": "...", "address": "...", "dob": "...", "valid_id": true}'
                            response = model.generate_content([prompt, img])
                            
                            raw = response.text.strip().replace("'", '"')
                            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                            elif "```" in raw: raw = raw.split("```")[1].strip()
                            
                            res = json.loads(raw)
                            if res.get('valid_id'):
                                # Create Identity Hash to prevent duplicates
                                identity_string = f"{res['name']}|{res['dob']}|{res['address']}".upper().strip()
                                identity_hash = hashlib.sha256(identity_string.encode()).hexdigest()
                                
                                # Check for duplicates
                                dup_check = supabase.table("profiles").select("id").eq("identity_hash", identity_hash).execute()
                                if dup_check.data:
                                    st.error("❌ Registration Blocked: This identity is already registered.")
                                    if st.button("Start Over"):
                                        st.session_state.reg_step = 1
                                        st.rerun()
                                else:
                                    st.session_state.reg_data.update(res)
                                    st.session_state.reg_data['identity_hash'] = identity_hash
                                    # Save the ID Face for later comparison
                                    st.session_state.reg_data['id_image'] = id_front.getvalue()
                                    st.session_state.reg_step = 3
                                    st.rerun()
                            else:
                                st.error("❌ Invalid ID: Could not detect a valid government document.")
                        except Exception as e:
                            st.error(f"OCR Error: {e}")

        elif st.session_state.reg_step == 3:
            st.info("📷 Capture the BACK of your Government ID. Focus on the barcode.")
            id_back = st.camera_input("Scan ID Barcode")
            if id_back:
                if st.button("Verify Barcode", type="primary", use_container_width=True):
                    with st.spinner("Authenticating Barcode..."):
                        try:
                            img = PIL.Image.open(id_back)
                            prompt = 'Read the PDF417 barcode data on the back of this ID. Return the raw text or a summary of the data. Respond ONLY with JSON: {"barcode_detected": true, "raw_data": "..."}'
                            response = model.generate_content([prompt, img])
                            
                            raw = response.text.strip().replace("'", '"')
                            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                            
                            res = json.loads(raw)
                            if res.get('barcode_detected'):
                                st.session_state.reg_step = 4
                                st.rerun()
                            else:
                                st.error("❌ Barcode not detected. Please ensure the back of the ID is clear and centered.")
                        except Exception as e:
                            st.error(f"Barcode Error: {e}")

        elif st.session_state.reg_step == 4:
            st.info("🤳 Final Step: Perform a live biometric scan to link your identity.")
            live_scan = st.camera_input("Live Biometric Scan")
            if live_scan:
                if st.button("Finalize Registration", type="primary", use_container_width=True):
                    with st.spinner("Performing Triple Verification..."):
                        try:
                            # 1. Compare Live Scan with ID Image Face
                            ref_img = PIL.Image.open(io.BytesIO(st.session_state.reg_data['id_image']))
                            live_img = PIL.Image.open(live_scan)
                            
                            # Zoom the live image to match previous UI standard
                            w, h = live_img.size
                            nw, nh = w/1.5, h/1.5
                            live_img = live_img.crop(((w-nw)/2, (h-nh)/2, (w+nw)/2, (h+nh)/2))
                            
                            prompt = """Verify:
                            1. Is the live scan a live person (liveness)?
                            2. Does the live person match the photo on the ID front?
                            Respond ONLY with JSON: {"liveness": true, "match": true}"""
                            
                            response = model.generate_content([prompt, ref_img, live_img])
                            raw = response.text.strip().replace("'", '"')
                            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
                            
                            res = json.loads(raw)
                            if res.get('liveness') and res.get('match'):
                                # TRIPLE VERIFIED - SAVE TO DATABASE
                                voter_id = hashlib.md5(f"{time.time()}{live_scan.getvalue()}".encode()).hexdigest()[:8].upper()
                                hashed_passcode = hashlib.sha256(st.session_state.reg_data['passcode'].encode()).hexdigest()
                                
                                # Upload live biometric ref
                                img_byte_arr = io.BytesIO()
                                live_img.save(img_byte_arr, format='JPEG')
                                current_bytes = img_byte_arr.getvalue()
                                
                                if upload_biometric(voter_id, current_bytes):
                                    supabase.table("profiles").insert({
                                        "voter_id": voter_id,
                                        "passcode_hash": hashed_passcode,
                                        "identity_hash": st.session_state.reg_data['identity_hash'],
                                        "full_name": st.session_state.reg_data['name'],
                                        "address": st.session_state.reg_data['address'],
                                        "dob": st.session_state.reg_data['dob']
                                    }).execute()
                                    
                                    st.session_state.voter_id = voter_id
                                    st.session_state.reg_step = 1 # Reset
                                    st.session_state.reg_data = {}
                                    st.session_state.show_login_dialog = False
                                    st.success(f"✅ Registration Triple-Verified! Voter ID: {voter_id}")
                                    st.balloons()
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("Failed to upload biometric record.")
                            else:
                                st.error("❌ Verification Failed: Biometric mismatch or liveness check failed.")
                        except Exception as e:
                            st.error(f"Verification Error: {e}")
        
        if st.session_state.reg_step > 1:
            if st.button("Cancel Registration"):
                st.session_state.reg_step = 1
                st.session_state.reg_data = {}
                st.session_state.show_login_dialog = False
                st.rerun()

    st.markdown("---")
    if st.button("Close Portal", use_container_width=True):
        st.session_state.show_login_dialog = False
        st.rerun()

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
                            voter_id = profile_res.data.get("voter_id")
                            
                            if voter_id:
                                # Set as pending and redirect to biometric verification
                                st.session_state.pending_voter_id = voter_id
                                st.session_state.current_view = "Login"
                                st.success("Account verified. Please complete biometric scan.")
                                st.rerun()
                            else:
                                st.warning("No Voter ID found for this account. Please register biometrics.")
                                st.session_state.current_view = "Home" # Or wherever
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
                    # Sign up with Supabase and explicitly set the redirect URL
                    # This prevents the localhost:3000 error and handles deployment automatically
                    res = supabase.auth.sign_up({
                        "email": reg_email, 
                        "password": reg_password,
                        "options": {
                            "email_redirect_to": get_redirect_url()
                        }
                    })
                    if res.user:
                        st.success("Account created! Please check your email for confirmation. After clicking the link, return here to Login.")
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
    # Using 'gemini-flash-latest' for stable, high-speed processing.
    # This identifier dynamically maps to the most reliable Flash model available.
    model = genai.GenerativeModel('gemini-flash-latest')
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
voter_status = f"{st.session_state.voter_id}" if st.session_state.voter_id else "Guest"
status_class = "verified" if st.session_state.voter_id else ""

# CSS Anchor for targeting the header row directly
st.markdown('<div id="header-anchor"></div>', unsafe_allow_html=True)

# Unified 3-column layout: [Logo, Spacer, AuthStack]
col_logo, col_spacer, col_auth = st.columns([3, 5, 2], vertical_alignment="center")

with col_logo:
    # ⚖️ LUCID Voting with 20px left buffer
    st.markdown('<h3 class="header-logo-text logo-buffer" style="margin: 0;">⚖️ LUCID Voting</h3>', unsafe_allow_html=True)

with col_spacer:
    st.write("") # Spring

with col_auth:
    # Combined vertical stack for Login and Badge, shifted 40px right
    st.markdown('<div class="auth-stack">', unsafe_allow_html=True)
    
    # Conditional Button: Login/Register OR Logout
    if st.session_state.voter_id:
        if st.button("Logout", key="header_logout_btn"):
            st.session_state.voter_id = None
            st.session_state.pending_voter_id = None
            # Sign out from Supabase if applicable
            try:
                supabase.auth.sign_out()
            except:
                pass
            st.rerun()
    else:
        # Row 1: Biometric Login/Register Portal
        if st.button("Register/Login", key="header_login_btn"):
            st.session_state.show_login_dialog = True
            st.rerun()
        
    if st.session_state.show_login_dialog:
        login_dialog()
        
    # Row 2: Status Badge (Guest/Voter ID)
    st.markdown(f'<span class="status-badge {status_class}" style="margin-top: 2px;">{voter_status}</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Remove the old query-param based trigger if present
if "auth" in st.query_params:
    st.query_params.clear()

# Main Content Area
st.markdown('<div id="main-anchor"></div>', unsafe_allow_html=True)

with st.container():
    if st.session_state.current_view == "Home":
        st.markdown('<h1 class="page-title">Federal Law Book</h1>', unsafe_allow_html=True)
        
        if supabase:
            try:
                # 1. Fetch Data
                response = supabase.table("bills").select("*").execute()
                if not response.data:
                    st.info("No laws found in the database. Use the Admin tab or import script to add laws.")
                else:
                    # Load into Pandas DataFrame
                    df = pd.DataFrame(response.data)
                    
                    # Sorting by section_number or ID (numeric sorting for section numbers if possible)
                    df = df.sort_values(by=['us_title', 'chapter', 'section_number'])

                    # 2. The "Law Book" UI - Hierarchical Grouping
                    us_titles = df['us_title'].unique()
                    
                    for utitle in us_titles:
                        with st.expander(f"📚 {utitle}", expanded=False):
                            title_df = df[df['us_title'] == utitle]
                            chapters = title_df['chapter'].unique()
                            
                            for chap in chapters:
                                with st.expander(f"📁 Chapter: {chap}", expanded=False):
                                    chap_df = title_df[title_df['chapter'] == chap]
                                    
                                    # 3. Section Display Cards
                                    for _, row in chap_df.iterrows():
                                        with st.container():
                                            st.markdown(f"### {row['section_number']} - {row['title']}")
                                            
                                            # Summary Area
                                            if row.get('simple_summary'):
                                                st.markdown(f"""
                                                <div class="info-box">
                                                    <strong>LUCID Summary (Neutral):</strong><br>
                                                    {row['simple_summary']}
                                                </div>
                                                """, unsafe_allow_html=True)
                                            else:
                                                # 4. The "Analyze" Button Logic
                                                if st.button(f"⚡ AI Analyze Section {row['section_number']}", key=f"analyze_{row['id']}"):
                                                    with st.spinner("AI is analyzing legal text..."):
                                                        try:
                                                            # Use gemini-2.0-flash-exp as requested
                                                            analysis_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                                                            prompt = f"Summarize this US Code section for a 5th grader. Keep it neutral and focus on what it does.\n\nSection Title: {row['title']}\n\nContent:\n{row['full_text']}"
                                                            
                                                            ai_response = analysis_model.generate_content(prompt)
                                                            summary_text = ai_response.text.strip()
                                                            
                                                            # Update Supabase
                                                            supabase.table("bills").update({"simple_summary": summary_text}).eq("id", row['id']).execute()
                                                            
                                                            st.success("Analysis Complete!")
                                                            time.sleep(1)
                                                            st.rerun()
                                                        except Exception as e:
                                                            st.error(f"Analysis Failed: {e}")

                                            # 5. Full Text Toggle
                                            with st.expander("📄 Show Full Legal Text"):
                                                st.write(row['full_text'])
                                            
                                            st.markdown("---")

            except Exception as e:
                st.error(f"Error loading Law Book: {e}")
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
        st.markdown('<h1 class="page-title">Biometric Identity Portal</h1>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <strong>Secure Biometric Access</strong><br>
                LUCID utilizes advanced iris and facial pattern recognition to verify voter identity. 
                Your biometric data is encrypted and stored in a private federal vault.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="scanner-guide">IRIS TARGET ZONE</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.write("Click below to initialize the high-resolution biometric scanner.")
            if st.button("Launch Biometric Scanner", type="primary", use_container_width=True):
                login_dialog()

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
            <p style="margin-top: 0.5rem; font-size: 0.75rem;">
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
                        "Summarize this legislation neutrally. Return ONLY a valid JSON object with the following keys: "
                        "'title' (simplified), 'simple_summary' (a neutral, 5th-grade reading level explanation of what the law actually does). "
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
