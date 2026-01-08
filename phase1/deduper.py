import os
import json
import anthropic
import re
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

# The file we want to clean
TARGET_FILE = 'master_feed.json'

SYSTEM_PROMPT = """
You are an expert News Editor. Your goal is to identify REDUNDANT stories in a news feed.

### INSTRUCTIONS
1. **Analyze**: Read the incoming list of news articles.
2. **Find Duplicates**: Look for articles covering the **exact same specific event** (e.g., "Fed raises rates" vs "Federal Reserve hikes interest").
   - If two stories are similar but offer different angles (e.g. "Fed raises rates" vs "Market crashes after Fed decision"), KEEP BOTH.
   - Only mark as duplicate if they convey the exact same core information.
3. **Decide**: For each group of duplicates, pick ONE winner to keep (the one with the best summary or highest importance_score).
4. **Output**: Return a JSON object containing a list of `remove_ids`—the IDs of the articles that should be DELETED.

### OUTPUT SCHEMA
{
  "remove_ids": [12, 45, 99] 
}
"""

def extract_json_from_text(text):
    try:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match: return match.group(1)
        return text 
    except: return text

def deduplicate_feed():
    if not os.path.exists(TARGET_FILE):
        print(f"Error: {TARGET_FILE} not found. Run tagger.py first!")
        return

    print(f"Loading {TARGET_FILE} for semantic deduplication...")
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get("articles", [])
    initial_count = len(articles)
    
    if initial_count == 0:
        print("No articles to deduplicate.")
        return

    # Create a "Lightweight" payload for the AI (saves tokens)
    ai_payload = []
    for art in articles:
        ai_payload.append({
            "id": art.get("id"),
            "headline": art.get("headline"),
            "source": art.get("source"),
            "summary": art.get("summary")
        })

    print(f"Sending {initial_count} articles to AI to find semantic duplicates...")
    
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001", # Your model
            max_tokens=4000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"### ARTICLES LIST\n{json.dumps(ai_payload, indent=2)}" 
                }
            ]
        )
        
        # Parse Response
        response_text = message.content[0].text
        clean_json = extract_json_from_text(response_text)
        response_data = json.loads(clean_json)
        
        # Identify IDs to remove
        ids_to_remove = set(response_data.get("remove_ids", []))
        
        if not ids_to_remove:
            print("No duplicates found. File remains unchanged.")
            return

        print(f"AI identified {len(ids_to_remove)} duplicates to remove: {ids_to_remove}")

        # Filter the original list
        final_articles = [art for art in articles if art["id"] not in ids_to_remove]

        # Overwrite the Master File
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            json.dump({"articles": final_articles}, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Feed reduced from {initial_count} to {len(final_articles)} articles.")
        print(f"Cleaned data saved to '{TARGET_FILE}'")

    except Exception as e:
        print(f"Error during deduplication: {e}")

if __name__ == "__main__":
    deduplicate_feed()