import os
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing Supabase keys in .env")
    exit()

supabase: Client = create_client(url, key)

def import_xml():
    file_path = "usc01.xml"
    print(f"Reading {file_path}...")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}. Make sure it is in this folder.")
        return

    soup = BeautifulSoup(content, "xml")
    
    main_tag = soup.find("main")
    if not main_tag:
        print("Error: Could not find <main> tag in XML.")
        return

    us_title_tag = main_tag.find("title")
    
    us_title_text = "Unknown Title"
    if us_title_tag:
        heading = us_title_tag.find("heading")
        if heading:
            us_title_text = heading.text
        else:
            us_title_text = us_title_tag.get_text().split("\n")[0]

    print(f"Found Law Group: {us_title_text}")
    
    chapters = us_title_tag.find_all("chapter") if us_title_tag else []
    
    rows_to_insert = []
    
    for chap in chapters:
        chap_heading = chap.find("heading")
        chapter_name = chap_heading.text if chap_heading else "Unknown Chapter"
        
        sections = chap.find_all("section")
        
        for sec in sections:
            num_tag = sec.find("num")
            heading_tag = sec.find("heading")
            content_tag = sec.find("content")

            sec_num = num_tag.text.strip() if num_tag else ""
            
            # --- THE FIX: FILTER OUT QUOTED SECTIONS ---
            # If the section number has a quote mark, it is likely inside a footnote/note.
            if '“' in sec_num or '"' in sec_num or "SEC." in sec_num:
                print(f"Skipping nested quote: {sec_num}")
                continue
            # -------------------------------------------

            bill_title = heading_tag.text.strip() if heading_tag else "No Title"
            
            if content_tag:
                full_text = content_tag.get_text(separator="\n\n").strip()
            else:
                full_text = "No text available."

            rows_to_insert.append({
                "us_title": us_title_text,
                "chapter": chapter_name,
                "section_number": sec_num,
                "title": bill_title,
                "full_text": full_text,
                "source_file": "usc01.xml"
            })
            
            print(f"Prepared: {sec_num} - {bill_title}")

    # Bulk Insert
    if rows_to_insert:
        print(f"Inserting {len(rows_to_insert)} clean rows into Supabase...")
        try:
            # Note: This will append to the table. 
            # Ideally, truncate the table first in Supabase SQL Editor if you want a fresh start.
            data, count = supabase.table("bills").insert(rows_to_insert).execute()
            print("Success! Import Complete.")
        except Exception as e:
            print(f"Error during upload: {e}")
    else:
        print("No sections found to import.")

if __name__ == "__main__":
    import_xml()