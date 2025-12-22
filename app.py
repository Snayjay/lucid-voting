import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
from web3 import Web3

# Load environment variables
load_dotenv()

# Configure Page
st.set_page_config(page_title="Lucid Voting", page_icon="⚖️", layout="wide")

st.title("⚖️ Lucid Voting")
st.markdown("### Educating citizens on US laws at a 5th-grade level.")

# Initialize API Keys (from .env)
gemini_key = os.getenv("GOOGLE_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)
    st.sidebar.success("✅ Gemini API Configured")
else:
    st.sidebar.warning("⚠️ Gemini API Key missing in .env")

if supabase_url and supabase_key:
    # supabase: Client = create_client(supabase_url, supabase_key)
    st.sidebar.success("✅ Supabase Configured")
else:
    st.sidebar.warning("⚠️ Supabase Credentials missing in .env")

# Basic App Structure
tab1, tab2, tab3 = st.tabs(["📜 Current Laws", "💬 Legislation Threads", "🗳️ Secure Voting"])

with tab1:
    st.header("Current & Proposed Legislation")
    st.info("Coming soon: Gemini-powered 5th grade level breakdowns of US laws.")

with tab2:
    st.header("Discussion Threads")
    st.info("Coming soon: Interactive threads to discuss and understand legislation.")

with tab3:
    st.header("Secure Blockchain Voting")
    st.info("Coming soon: Iris scanning and blockchain-backed voting system.")

st.sidebar.divider()
st.sidebar.info("Built for Lucid-Voting project.")

