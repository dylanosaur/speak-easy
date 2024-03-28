
import sqlite3
from flask import request

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
             score INTEGER, enabled INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS builds
             (id INTEGER PRIMARY KEY, git_hash TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, cohort_hash TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS conversations
             (id INTEGER PRIMARY KEY, user INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, messages TEXT)''')
      
    conn.commit()
    conn.close()

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
