import scraper
import tagger
import deduper  # <--- Import the new script
import time

def run_pipeline():
    print("==========================================")
    print("   STARTING NEWS AGGREGATION PIPELINE     ")
    print("==========================================\n")

    # --- STEP 1: SCRAPING ---
    print("--- STEP 1: SCRAPING RSS FEEDS ---")
    try:
        scraper.main()
        print(">> Scraping completed.\n")
    except Exception as e:
        print(f"!! CRITICAL ERROR IN SCRAPER: {e}")
        return 

    time.sleep(1) # Short pause for file I/O safety

    # --- STEP 2: TAGGING ---
    print("--- STEP 2: AI TAGGING & FILTERING ---")
    try:
        tagger.tag_news_feed()
        print(">> Tagging completed.\n")
    except Exception as e:
        print(f"!! CRITICAL ERROR IN TAGGER: {e}")
        return

    time.sleep(1)

    # --- STEP 3: DEDUPLICATION ---
    print("--- STEP 3: SEMANTIC DEDUPLICATION ---")
    try:
        deduper.deduplicate_feed()
        print(">> Deduplication completed.\n")
    except Exception as e:
        print(f"!! CRITICAL ERROR IN DEDUPER: {e}")
        return

    print("==========================================")
    print("       PIPELINE FINISHED SUCCESSFULLY     ")
    print("==========================================")

if __name__ == "__main__":
    run_pipeline()