import sqlite3
import hashlib

# New Database Name
DB_FILE = 'user_info.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_user_id(email):
    # Short hash of email for a clean ID
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()[:8]
    return f"user_{email_hash}"

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # The "One Table to Rule Them All"
    # newsletter_content stores the final output from the AI
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            preferences TEXT,
            newsletter_content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database {DB_FILE} initialized successfully.")

def add_user(email, first_name, last_name, preferences):
    conn = get_db_connection()
    c = conn.cursor()
    user_id = generate_user_id(email)
    
    try:
        # Insert or Update (Upsert)
        # Note: We do NOT overwrite newsletter_content here, so we don't lose old emails when updating profile
        c.execute('''
            INSERT INTO users (user_id, email, first_name, last_name, preferences)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                preferences=excluded.preferences
        ''', (user_id, email, first_name, last_name, preferences))
        
        conn.commit()
        return user_id
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def save_newsletter(user_id, content):
    """Saves the final AI-generated newsletter to the user's row."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET newsletter_content = ? WHERE user_id = ?', (content, user_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
