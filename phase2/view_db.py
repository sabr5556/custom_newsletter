import sqlite3
import json

conn = sqlite3.connect('user_info.db')
c = conn.cursor()

# Get all rows
c.execute("SELECT * FROM user_selections")
rows = c.fetchall()

print(f"--- Database Content ({len(rows)} users) ---\n")

for user_id, data_str in rows:
    data = json.loads(data_str)
    article_count = len(data.get('articles', []))
    print(f"User: {user_id}")
    print(f"Articles: {article_count}")
    # Print the first headline as a sanity check
    if article_count > 0:
        first_headline = data['articles'][0]['headline']
        print(f"Sample Headline: {first_headline}")
    print("-" * 20)

conn.close()
