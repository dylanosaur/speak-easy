
import sqlite3
from flask import request
from util import get_build_hash

# SQLite database file path
DB_FILE = 'requests.db'

def create_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (ip TEXT PRIMARY KEY, count INTEGER, build TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ThreadComments
             (id INTEGER PRIMARY KEY, url TEXT, input TEXT, comment TEXT, success INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS prompts
             (id INTEGER PRIMARY KEY, prompt TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
             score INTEGER, enabled INTEGER, prompt_prefix TEXT, prompt_topics TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS builds
             (id INTEGER PRIMARY KEY, git_hash TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, cohort_hash TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS conversations
             (id INTEGER PRIMARY KEY, user TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, messages TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS translations
             (id INTEGER PRIMARY KEY, user TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
              input TEXT, output TEXT, lang TEXT)''')
      
    conn.commit()
    conn.close()


class Translations:
    def __init__(self):
        self.db = DB_FILE

    def insert(self, user, input, output, lang):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO Translations (user, input, output, lang) VALUES (?, ?, ?, ?)", (user, input, output, lang))
            conn.commit()   

class Builds:
    def __init__(self):
        self.db = DB_FILE

    def insert(self, git_hash):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO builds (git_hash) VALUES (?)", (git_hash,))
            conn.commit()
    
    def insert_if_not_exists(self, git_hash):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            # Check if the git_hash already exists in the database
            c.execute("SELECT COUNT(*) FROM builds WHERE git_hash = ?", (git_hash,))
            count = c.fetchone()[0]
            if count == 0:
                # If git_hash does not exist, insert it
                c.execute("INSERT INTO builds (git_hash) VALUES (?)", (git_hash,))
                conn.commit()

class Users:
    def __init__(self):
        self.db = DB_FILE

    def insert(self, cohort_hash):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (cohort_hash) VALUES (?)", (cohort_hash,))
            conn.commit()

class Conversations:
    def __init__(self):
        self.db = DB_FILE

    def insert(self, user_id, messages):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO conversations (user, messages) VALUES (?, ?)", (user_id, messages))
            conn.commit()
            # Return the ID of the inserted conversation
            return c.lastrowid

    def query_by_id(self, conversation_id):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            return c.fetchone()

    def update_by_id(self, conversation_id, new_messages):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("UPDATE conversations SET messages = ? WHERE id = ?", (new_messages, conversation_id))
            conn.commit()
    
    def get_all(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM conversations")
            conversations = c.fetchall()
        return conversations


import datetime
class Prompts:
    
    def __init__(self):
        self.db = DB_FILE

    def get_all(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM prompts")
            return c.fetchall()

    def get_latest(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM prompts ORDER BY timestamp DESC LIMIT 1")
            return c.fetchone()

    def get_highest_score(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM prompts ORDER BY score DESC LIMIT 1")
            return c.fetchone()

    def insert(self, prompt_text, score, prompt_prefix, prompt_topics, enabled=1):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO prompts (prompt, score, enabled, prompt_prefix, prompt_topics) VALUES (?, ?, ?, ?, ?)", (prompt_text, score, enabled, prompt_prefix, prompt_topics))
            conn.commit()

    def get_prompts_from_today(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            today_date = datetime.datetime.now().strftime('%Y-%m-%d')
            # Execute the query
            c.execute("SELECT * FROM prompts WHERE DATE(timestamp) = ?", (today_date,))
            prompts_today = c.fetchall()
            return prompts_today

class Requests:
    
    def __init__(self):
        self.db = DB_FILE

    
    def get_logged_results(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM requests")
        results = c.fetchall()
        conn.close()
        return results

    def get_build_and_count(self):
        conn = sqlite3.connect(self.db)  # Replace 'your_database.db' with your database file path
        c = conn.cursor()
        c.execute("SELECT build, count FROM requests")
        data = c.fetchall()
        conn.close()
        return data

    def log_user(self, ip_address, build_hash):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()

        # Check if the IP address already exists in the database
        c.execute("SELECT * FROM requests WHERE ip=?", (ip_address,))
        row = c.fetchone()

        if row:
            # If IP exists, increment the count
            count = row[1] + 1
            c.execute("UPDATE requests SET count=? WHERE ip=?", (count, ip_address))
        else:
            # If IP doesn't exist, insert a new record with count=1
            c.execute("INSERT INTO requests VALUES (?, 1, ?)", (ip_address,build_hash))
        
        conn.commit()
        conn.close()

        
class ThreadComments:

    def __init__(self):
        self.db = DB_FILE

    # Function to insert a comment into the database
    def insert_comment(self, url, input_text, comment_text):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO ThreadComments (url, input, comment, success) VALUES (?, ?, ?, ?)", (url, input_text, comment_text, 0))
        conn.commit()
        conn.close()
        print('comment added', url, input_text, comment_text)

    # Function to read and print all comments from the database
    def print_all_comments(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM ThreadComments")
        comments = c.fetchall()
        for comment in comments:
            print(f"ID: {comment[0]}, URL: {comment[1]}, Input: {comment[2]}, Comment: {comment[3]}")
        conn.close()

    def get_all(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()

        # Query the database to fetch ThreadComments
        c.execute("SELECT * FROM ThreadComments")
        comments = c.fetchall()

        # Close the database connection
        conn.close()

        return comments

    # Function to return the count of comments
    def count_comments(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ThreadComments")
        count = c.fetchone()[0]
        conn.close()

        return count

    def check_url_existence(self, url):
        conn = sqlite3.connect(self, self.db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ThreadComments WHERE url=? AND success=1", (url,))
        result = c.fetchone()[0]

        conn.close()

        return result > 0

    def mark_url_as_success(self, url):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ThreadComments WHERE url=? AND success=0", (url,))
        result = c.fetchone()[0]
        if result > 0:
            c.execute("UPDATE ThreadComments SET success = 1 WHERE url=?", (url,))
            conn.commit()  # Commit the transaction
        conn.close()

        return result > 0
