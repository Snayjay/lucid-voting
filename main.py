import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
st.set_page_config(page_title="LUCID", page_icon="⚖️", layout="wide")

# Initialize API Keys
gemini_key = os.getenv("GEMINI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Initialize Gemini
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    st.error("Missing GEMINI_API_KEY in .env")

# Initialize Supabase
supabase: Client = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
else:
    st.error("Missing Supabase credentials in .env")

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Home", "Admin: Add Bill"])

st.title("⚖️ LUCID")
st.subheader("Legislative Understanding Creates Informed Decisions")

if menu == "Home":
    st.header("Latest Legislation")
    
    if supabase:
        try:
            # Query last 5 bills
            response = supabase.table("bills").select("*").order("created_at", desc=True).limit(5).execute()
            bills = response.data
            
            if not bills:
                st.info("No bills found in the database yet.")
            
            for bill in bills:
                with st.expander(f"📜 {bill.get('title', 'Untitled Bill')}"):
                    st.markdown("### Simple Summary")
                    st.write(bill.get('simple_summary', 'No summary available.'))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success("### Pros")
                        pros = bill.get('pros', [])
                        if isinstance(pros, list):
                            for pro in pros:
                                st.write(f"✅ {pro}")
                        else:
                            st.write(pros)
                            
                    with col2:
                        st.error("### Cons")
                        cons = bill.get('cons', [])
                        if isinstance(cons, list):
                            for con in cons:
                                st.write(f"❌ {con}")
                        else:
                            st.write(cons)
        except Exception as e:
            st.error(f"Error fetching bills: {e}")
    else:
        st.warning("Supabase not configured.")

elif menu == "Admin: Add Bill":
    st.header("Admin: Add New Bill")
    
    bill_text = st.text_area("Paste Bill Text", height=300)
    analyze_button = st.button("Analyze & Save")
    
    if analyze_button:
        if not bill_text:
            st.warning("Please paste some bill text first.")
        elif not gemini_key or not supabase:
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
                    st.text(response.text) # For debugging
                except Exception as e:
                    st.error(f"An error occurred: {e}")

st.sidebar.divider()
st.sidebar.info("Educating users on current US laws.")

