import os
import json
import sqlite3
import anthropic
from dotenv import load_dotenv, find_dotenv
import user_manager 

load_dotenv(find_dotenv())
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PHASE1_DIR = os.path.join(os.path.dirname(__file__), '..', 'phase1')
MASTER_FEED_PATH = os.path.join(PHASE1_DIR, 'master_feed.json')

# --- STEP A: FILTER (Matchmaker) ---
def filter_news(preferences, all_articles):
    """Returns a list of articles relevant to the user."""
    system_prompt = "You are a news filter. Select the top 5 articles from the list that strictly match the user's preferences."
    
    user_content = f"PREFERENCES: {preferences}\n\nARTICLES: {json.dumps(all_articles)}"
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}]
    )
    return message.content[0].text

# --- STEP C: WRITER (Haiku) ---
def write_newsletter(articles_text, user_name):
    """Writes the final email."""
    system_prompt = "You are a master newsletter publisher. Write a professional, engaging daily briefing."
    
    # Updated Prompt for Length and Depth
    prompt = f"""
    You are an expert newsletter editor writing a daily briefing for {user_name}. 
    Your goal is to synthesize the provided source material into a professional, high-signal newsletter.

    SOURCE MATERIAL:
    {articles_text}

   ### FORMATTING & CONTENT INSTRUCTIONS

    **1. Subject Line**
    - Must be punchy, relevant, and concise. 
    - Focus on the main Deep Dive topic.

    **2. Executive Summary**
    - Provide 3-5 bullet points summarizing the top stories and any major global news mentioned in the other news section.
    - Keep them scannable and high-level.

    **3. Deep Dives**
    - Select the two most significant stories.
    - **Formatting**: Do NOT number these stories. Use a **Bold Headline** for each.
    - **Content**: For each story, write a cohesive 300-350 word analysis. 
    - **Structure**: Do NOT use sub-headers (like "Context" or "Why it Matters"). Instead, write 2-3 paragraphs where the first paragraph establishes the context/what happened, and the following paragraphs explain why it matters and the future implications.

    **4. Company Watch (Conditional Section)**
    - strict rule: Only create this section if the provided Source Material contains news specifically about companies mentioned in the user's preferences.
    - If no news is found for those specific companies, **omit this entire section (including the header)**.
    - If found, summarize the updates, specifically looking for stock swings or valuation changes.

    **5. Other News**
    - Brief summaries (1-2 sentences) of the remaining stories not covered in Deep Dives.
    - Also provide brief summaries on any major global news stories not covered in Deep Dives.

    **6. Signoff**
    - End exactly with: 

        "
        *NEW LINE*
        *IN ITALICS* Daily news curated for you *NEW LINE*
        *BACK TO NORMAL TEXT* From, *NEW LINE*
        The Daily Distill"

    ### STYLE GUIDELINES
    - **Tone**: Professional and friendly. Think "smart colleague," not "robot."
    - **Negative Constraint**: Do NOT use generic introductions like "Here is your news." Start immediately with the Executive Summary.
    - **Visuals**: Use standard Markdown. No colored text or code blocks.
    """
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000, # Increased for longer output
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw_text = message.content[0].text
    
    # FIX: Escape special characters for Streamlit Markdown
    clean_text = raw_text.replace("$", r"\$") 
    clean_text = clean_text.replace("_", r"\_") 
    
    return clean_text

# --- MAIN CONTROLLER ---
def generate_for_user(user_id):
    # 1. Get User Data
    conn = user_manager.get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user: return "User not found."

    # 2. Get News Data
    if not os.path.exists(MASTER_FEED_PATH):
        return "Error: master_feed.json not found. Run Phase 1."

    with open(MASTER_FEED_PATH, 'r') as f:
        feed = json.load(f)
    
    print(f"--- Pipeline Started for {user['first_name']} ---")
    

    print("1. Filtering News...")
    relevant_content = filter_news(user['preferences'], feed['articles'])
    
    print("2. Writing Newsletter...")
    final_email = write_newsletter(relevant_content, user['first_name'])
    
    user_manager.save_newsletter(user_id, final_email)
    print(">> Done! Newsletter saved to Database.")
    
    return final_email
