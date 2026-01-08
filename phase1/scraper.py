from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from dateutil import tz

# Configuration
SOURCES_FILE = 'sources.json'
OUTPUT_FILE = 'news_feed.json'

def parse_feed(url, tags, site_name, category_name):
    """Fetches a single RSS URL and returns a list of article objects."""
    articles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Define timezone mapping for ambiguous abbreviations
    tz_mapping = {
        "EST": tz.gettz("US/Eastern"),
        "EDT": tz.gettz("US/Eastern"),
        "CST": tz.gettz("US/Central"),
        "CDT": tz.gettz("US/Central"),
        "MST": tz.gettz("US/Mountain"),
        "MDT": tz.gettz("US/Mountain"),
        "PST": tz.gettz("US/Pacific"),
        "PDT": tz.gettz("US/Pacific")
    }

    # Define the cutoff time (24 hours ago), ensuring it is timezone-aware (UTC)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, features='xml')
        items = soup.find_all(tags['article']) 

        for item in items:
            # 1. Extract Date first to filter immediately
            date_node = item.find(tags['date'])
            date_str = date_node.text.strip() if date_node else str(datetime.now())
            
            try:
                # Parse the date string into a datetime object
                # UPDATED: Pass tzinfos to fix the EST warning
                pub_date = date_parser.parse(date_str, tzinfos=tz_mapping)
                
                # If the date has no timezone (naive), assume UTC to compare safely
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                # DISCARD if older than 24 hours
                if pub_date < cutoff_time:
                    continue 

            except Exception:
                # If date parsing fails, we assume it's new enough to keep
                pass

            # 2. Title
            title_node = item.find(tags['title'])
            title = title_node.text.strip() if title_node else "N/A"

            # 3. Link
            link_node = item.find(tags['link'])
            link = "N/A"
            if link_node:
                link = link_node.text.strip()
                if tags.get('link_attr'): 
                    link = link_node.get(tags['link_attr'])

            # 4. Summary
            summary_node = item.find(tags['summary'])
            summary = "N/A"
            if summary_node:
                raw_text = summary_node.text
                if "<" in raw_text and ">" in raw_text:
                    summary = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ", strip=True)[:300]
                else:
                    summary = raw_text.strip()[:300]

            articles.append({
                "source": site_name,
                "category": category_name,
                "headline": title,
                "date": date_str,
                "summary": summary,
                "link": link
            })
            
    except Exception as e:
        print(f"Error reading {url}: {e}")

    return articles

def process_feeds():
    """Main logic: reads sources, loops through them, saves output."""
    with open(SOURCES_FILE, 'r') as f:
        sources = json.load(f)

    all_articles = []

    for site_name, site_info in sources.items():
        print(f"--- Processing: {site_name} ---")
        tags = site_info.get("tags")
        
        for category, url in site_info.get("categories", {}).items():
            print(f"   Fetching: {category}")
            new_articles = parse_feed(url, tags, site_name, category)
            all_articles.extend(new_articles)

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"articles": all_articles}, f, indent=4, ensure_ascii=False)
    
    print(f"\nSuccess! {len(all_articles)} articles (from last 24h) saved to '{OUTPUT_FILE}'")

def main():
    process_feeds()

if __name__ == "__main__":
    main()