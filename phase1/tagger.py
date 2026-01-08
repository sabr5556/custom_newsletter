import os
import json
import anthropic
import re
import time
from dotenv import load_dotenv, find_dotenv

# 1. Load Environment Variables
load_dotenv(find_dotenv())
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("API Key not found! Make sure ANTHROPIC_API_KEY is in your .env file.")

client = anthropic.Anthropic(api_key=api_key)

# 2. Define the System Prompt (Paste the FINAL prompt we wrote previously below)
SYSTEM_PROMPT = """
You are an advanced news aggregation AI. Your goal is to curate a high-signal news feed by filtering out noise and classifying important stories.

### INSTRUCTIONS

1. **Analyze & Filter**: 
   Read the provided news summaries. Select ONLY articles that represent significant developments, such as:
   - Acquisitions, mergers, and major investments.
   - Product launches, recalls, or breakthroughs.
   - Legislative changes, geopolitical shifts, or conflicts.
   - Major controversies or legal actions.
   
   **DISCARD** articles that are:
   - "Top 10" lists, buying guides, or reviews.
   - Minor incremental updates (e.g., "Game server maintenance").
   - Opinion pieces, editorials, or advice columns.

   **Clean**: 
   - Rewrite headlines to be purely factual (remove clickbait like "You won't believe...").
   - Rewrite summaries to be high-signal and objective.

2. **Tag**:
   Assign exactly ONE **Primary Tag** and up to TWO **Secondary Tags** from the lists below. If no secondary tag fits, leave that field empty

3. **Score**
    - Assign an `importance_score` (1-10) based on global impact.
   - 10 = Historic event / Major Market Crash.
   - 5 = Standard corporate news / Earnings beat.
   - 1 = Minor bug fix / "Top 10" list / Advertisement.

4. **Format Output**:
   You must respond with a valid JSON object containing a list of selected articles. 
   Preserve the original `link`, `date`, and `source`.
   Add a simple numerical `id` (1, 2, 3...) to each article.
   Schema:
   {
      "articles": [
         {
            "id":"numerical id",
            "headline": "Article Title",
            "summary": "A one-sentence summary of the event.",
            "primary_tag": "Tag Name",
            "secondary_tags": ["Tag A", "Tag B"],
            "source":"specific news outlet",
            "date":"YYYY-MM-DD HH:mm",
            "importance_score": integer,
            "link":"article link"
         }
      ]
   }

### TAG LISTS

   **Primary Tags:**
Global Affairs & Politics, Economy & Macro, Finance & Investing, Technology, Defense & Security, Science & Environment, Health & Society, Entertainment & Culture, Sports, Crime & Law

**Secondary Tags:**
- **Politics & Society:** Geopolitics, International Relations, United Nations, NATO, G7/G20 Summits, Elections, Legislation, Executive Orders, Supreme Court, Lobbying, Human Rights, Immigration, Refugees, Border Security, Civil Unrest, Protests, Terrorism, Diplomacy, Sanctions, Trade Agreements, Espionage, Urban Planning, Smart Cities, Public Infrastructure, Education Policy, Student Loans.
- **Economics:** Federal Reserve, Central Banks, Monetary Policy, Interest Rates, Inflation, CPI/PPI, GDP Growth, Recession Risk, Labor Market, Unemployment, Strikes/Unions, Supply Chain, Manufacturing, Trade Deficit, Consumer Confidence, Retail Sales, Housing Market, Mortgages.
- **Finance:** Stock Market, S&P 500, Nasdaq, Earnings Reports, IPOs, Mergers & Acquisitions, Venture Capital, Startups, Cryptocurrency, Bitcoin, Ethereum, DeFi, Stablecoins, Blockchain Regulation, Commodities, Oil & Gas, Gold & Metals, Personal Finance, Retirement Planning, Family Office.
- **Technology:** Artificial Intelligence, Generative AI, LLMs, Machine Learning, Neural Networks, AI Ethics, AI Regulation, Cybersecurity, Hacking, Ransomware, Data Privacy, Antitrust, Big Tech (FAANG), Semiconductors, Chip Manufacturing, Quantum Computing, Cloud Computing, SaaS, Enterprise Software, Data Centers, Consumer Electronics, Smartphones, Wearables, AR/VR/XR, 5G/6G Networks, Open Source.
- **Defense:** Military Strategy, Defense Spending, Arms Deals, Weapons Systems, AI Defense Tech, Autonomous Weapons, Drone Warfare, Unmanned Systems, Nuclear Proliferation, Ballistic Missiles, Arms Control, Intelligence Community, Surveillance, Counterterrorism, Special Operations, Space Force, Satellite Warfare, Hypersonics.
- **Science:** Climate Change, Carbon Emissions, Extreme Weather, Renewable Energy, Solar Power, Wind Power, Nuclear Fusion, Electric Vehicles (EVs), Battery Tech, Space Exploration, NASA, SpaceX, Mars Missions, Astronomy, Biotech, Genetics, CRISPR, Pharmaceuticals, Medical Devices, Materials Science, Superconductors.
- **Culture & Sports:** Streaming Services, Box Office, Hollywood, Music Industry, PC Gaming, Console Gaming, Esports, Game Development, Social Media Trends, Influencer Culture, Art & Design, NFL, NBA, MLB, NHL, FIFA/Soccer, Premier League, F1/Motorsport, Sports Betting, NCAA/College Sports, NIL deals, Recruitment, Injuries.
- **Law:** Violent Crime, Mass Shootings, Gun Control, White Collar Crime, Fraud, Money Laundering, Law Enforcement, Criminal Justice Reform, Drug Trafficking, Opioid Crisis, Healthcare Insurance, Medicare/Medicaid.

"""

def extract_json_from_text(text):
    """
    Robustly extracts JSON from the AI response by finding the outer-most brackets.
    """
    try:
        # Match content between the first { and last }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return text 
    except Exception:
        return text

def process_batch(batch_articles, batch_index):
    """
    Sends a small batch of articles to the AI for processing.
    """
    # Create a clean input JSON string for this batch
    batch_input = json.dumps({"articles": batch_articles}, indent=2)
    
    print(f"   > Processing batch {batch_index} ({len(batch_articles)} articles)...")
    batch_start_time = time.time()  # <--- Start Batch Timer
    
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307", # Note: Updated to correct model ID format if needed
            max_tokens=4000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"### INPUT DATA\n{batch_input}"
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Clean and Parse
        clean_json = extract_json_from_text(response_text)
        data = json.loads(clean_json)
        
        batch_end_time = time.time()  # <--- End Batch Timer
        duration = batch_end_time - batch_start_time
        print(f"     -> Batch {batch_index} finished in {duration:.2f} seconds.") # <--- Print Duration
        
        return data.get("articles", [])

    except json.JSONDecodeError:
        print(f"   !!! JSON Error in batch {batch_index}. Skipping this batch.")
        return []
    except Exception as e:
        print(f"   !!! Error in batch {batch_index}: {e}")
        return []

def tag_news_feed():
    input_file = 'news_feed.json'
    output_file = 'master_feed.json'
    
    # --- CONFIG: Output Limit ---
    MAX_ARTICLES_LIMIT = 1000
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run scraper.py first!")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    all_raw_articles = raw_data.get("articles", [])
    total_found = len(all_raw_articles)
    
    # --- LIMIT LOGIC ---
    if MAX_ARTICLES_LIMIT and total_found > MAX_ARTICLES_LIMIT:
        print(f"Limiting input from {total_found} to {MAX_ARTICLES_LIMIT} articles.")
        all_raw_articles = all_raw_articles[:MAX_ARTICLES_LIMIT]
    else:
        print(f"Processing all {total_found} articles.")
    
    # --- BATCHING LOGIC ---
    BATCH_SIZE = 20
    final_tagged_list = []
    
    # Start Total Timer
    total_start_time = time.time() # <--- Start Total Timer
    
    # Loop through list in chunks of BATCH_SIZE
    for i in range(0, len(all_raw_articles), BATCH_SIZE):
        batch = all_raw_articles[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        # Send to AI
        tagged_batch = process_batch(batch, batch_num)
        
        # Accumulate results
        if tagged_batch:
            final_tagged_list.extend(tagged_batch)

    # End Total Timer
    total_end_time = time.time() # <--- End Total Timer
    total_duration = total_end_time - total_start_time

    # --- POST-PROCESSING ---
    print("Assigning IDs and saving...")
    for index, article in enumerate(final_tagged_list, 1):
        article['id'] = index

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"articles": final_tagged_list}, f, indent=4, ensure_ascii=False)
            
    print(f"Success! {len(final_tagged_list)} articles saved to '{output_file}'")
    
    # Print formatted total time
    minutes = int(total_duration // 60)
    seconds = int(total_duration % 60)
    print(f"Total processing time: {minutes}m {seconds}s") # <--- Print Total Duration

if __name__ == "__main__":
    tag_news_feed()