from flask import Flask, request, jsonify, render_template, session
import os

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
client = OpenAI()

import subprocess
build_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'])[:6].decode()
print('build hash', build_hash)

from logger import create_custom_logger

app_logger = create_custom_logger(f'app-{build_hash}.log')
headers_logger = create_custom_logger(f'headers.log')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

import hashlib

def hash_ip(ip_address):
    # Convert IP address to bytes
    ip_bytes = ip_address.encode('utf-8')

    # Calculate SHA-256 hash
    hashed_ip = hashlib.sha256(ip_bytes).hexdigest()

    return hashed_ip



import sqlite3
from flask import request

# SQLite database file path
DB_FILE = 'requests.db'

def create_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (ip TEXT PRIMARY KEY, count INTEGER, build TEXT)''')
    # Create the ThreadComments table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS ThreadComments
             (id INTEGER PRIMARY KEY, url TEXT, input TEXT, comment TEXT, success INTEGER)''')

    conn.commit()
    conn.close()

create_table()

# Function to insert a comment into the database
def insert_comment(url, input_text, comment_text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO ThreadComments (url, input, comment, success) VALUES (?, ?, ?, ?)", (url, input_text, comment_text, 0))
    conn.commit()
    conn.close()
    print('comment added', url, input_text, comment_text)

# Function to read and print all comments from the database
def print_all_comments():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM ThreadComments")
    comments = c.fetchall()
    for comment in comments:
        print(f"ID: {comment[0]}, URL: {comment[1]}, Input: {comment[2]}, Comment: {comment[3]}")
    conn.close()

# Function to return the count of comments
def count_comments():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ThreadComments")
    count = c.fetchone()[0]
    conn.close()

    return count

def check_url_existence(url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ThreadComments WHERE url=? AND success=1", (url,))
    result = c.fetchone()[0]

    conn.close()

    return result > 0

def mark_url_as_success(url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ThreadComments WHERE url=? AND success=0", (url,))
    result = c.fetchone()[0]
    if result > 0:
        c.execute("UPDATE ThreadComments SET success = 1 WHERE url=?", (url,))
        conn.commit()  # Commit the transaction
    conn.close()

    return result > 0

from functools import wraps
def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):        
        create_table()
        ip_address = request.remote_addr
        try:
            ip_address = request.headers['X-Real-IP']
        except:
            print('unable to extract ip', request.headers)
        ip_address = hash_ip(ip_address)
        conn = sqlite3.connect(DB_FILE)
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

        return func(*args, **kwargs)
    return wrapper


conversation_history = []

def translate_text(text, target_language='en'):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": f"You are a translation to translate into {target_language}. Translate the input to {target_language}."},
            {"role": "user", "content": text}
        ]
    )

    text_response = completion.choices[0].message.content
    return text_response

import json

def generate_gpt_response(user_input, target_language="spanish"):

    if 'conversation' not in session:
        session['conversation'] = json.dumps({"data":
            [
                {"role": "system", "content": f"You are a tool to help someone learn {target_language}. \
                Just respond in {target_language} and continue the conversation. \
                Use beginner-intermediate level words and phrases and limit your response to one sentence and then one question"},
            ]
        })

    conversation = json.loads(session['conversation'])
    conversation['data'].append(
        {"role": "user", "content": user_input}
    )

    print('generating response using', target_language)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation['data']
    )

    text_response = completion.choices[0].message.content

    conversation['data'].append(
        {"role": "user", "content": text_response}
    )
    session['conversation'] = json.dumps(conversation)
    
    user_ip = '<ip>'
    try:
        user_ip_raw = request.headers['X-Real-IP']
        user_ip = hash_ip(user_ip_raw)[:6]
    except:
        pass

    app_logger.debug(f'ip:{user_ip} - lang:{target_language} - input: {user_input} - response: {text_response}')
    return text_response, 'empty comment'

def generate_gpt_response_reddit_comment(user_input, recommend_speak_easy=False):

    messages = [
        {"role": "system", "content": f"You are helping me train an anti bot detection system. The user input\
            will be a thread on a social media site. You should generate a reasonable comment for the topic. \
            Try to shorter sentences as if you were typing them out on a phone and you dont care much. \
            You are encouraged to be a little blunt and direct, and its okay if you lightly criticize the topic or slightly disagree with the other comment.\
            No exclamation punctuation.\
            Limit your response to 1-2 sentences. Try not to repeat any of the words they use in their comment. \
            Your comment should contribute a fresh idea to the conversation"},
        {"role": "user", "content": user_input}
    ]

    if recommend_speak_easy:
        messages[0]['content'] += "If they might benefit from a language learning tool then suggest that\
            try out https://speak-ez.net where they can practice learning a new language by having conversations. \
            you must use the URL as provided. Tell them something like \
            'i spun up this tiny website a few weeks ago and am hoping i can help people learn a new language by having conversations. \
            give it a try and if you have feedback id love to hear it!' "
        
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    text_response = completion.choices[0].message.content

    text_response = text_response.replace("!", ".").replace("SpeakEZ", "https://speak-ez.net").replace('"', '').replace("'", "")

    return text_response

def get_logged_results():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    results = c.fetchall()
    conn.close()
    return results

@app.route('/activity')
def admin():
    results = get_logged_results()
    return render_template('activity.html', results=results)

# Main route for receiving user input and generating responses
@app.route('/ask', methods=['POST'])
@log_request
def ask():

    target_language =  request.args.get('lang', 'spanish')
    data = request.get_json()
    user_input = data['input']

    # Append user input to conversation history
    conversation_history.append({'role': 'user', 'message': user_input})

    text_response, comment = generate_gpt_response(user_input, target_language=target_language)

    # Append ChatGPT's response to conversation history
    conversation_history.append({'role': 'assistant', 'message': text_response})

    # Return the response to the user
    return jsonify({"response": text_response, "english": translate_text(text_response), "comment": comment})

# Main route for receiving user input and generating responses
@app.route('/translate_and_ask', methods=['POST'])
@log_request
def translate_and_ask():
    data = request.get_json()
    user_input = data['input']

    target_language =  request.args.get('lang', 'spanish')

    translated_input = translate_text(user_input, target_language=target_language)
    text_response, comment = generate_gpt_response(translated_input, target_language=target_language)

    # Return the response to the user
    return jsonify({"response": text_response, "english": translate_text(text_response), "comment": comment, 'translated_user_input': translated_input})


# Main route for receiving user input and generating responses
@app.route('/reddit_response', methods=['POST'])
def reddit_response():
    data = request.get_json()
    user_input = data['input']
    url = data['url']

    url_already_processed = check_url_existence(url)
    if url_already_processed:
        print('url has already been processed', url)
        text_response = None
    else:
        comment_count = count_comments()
        recommend_enabled = comment_count % 30 == 0
        print('recommend is enabled', recommend_enabled, comment_count)
        text_response = generate_gpt_response_reddit_comment(user_input, recommend_speak_easy=recommend_enabled)

        insert_comment(url, user_input, text_response)

    # Return the response to the user
    return jsonify({"response": text_response})

@app.route('/reddit_response_success', methods=['POST'])
def reddit_response_success():
    data = request.get_json()
    url = data['url']

    mark_url_as_success(url)
    return jsonify({"data": "success"})

# Route to display the ThreadComments in a table
@app.route('/thread_comments')
def show_comments():
    # Connect to the SQLite database
    conn = sqlite3.connect('requests.db')
    c = conn.cursor()

    # Query the database to fetch ThreadComments
    c.execute("SELECT * FROM ThreadComments")
    comments = c.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template with comments data
    return render_template('comments.html', comments=comments)


# Route for retrieving conversation history
@app.route('/conversation', methods=['GET'])
def get_conversation():
    return jsonify(conversation_history)


# Clear conversation history
@app.route('/clear', methods=['DELETE'])
def clear_conversation():
    conversation_history.clear()
    return jsonify({"message": "Conversation history cleared."})

@app.route('/', methods=['GET'])
def index():
    try:
        headers_logger.debug(json.dumps(dict(request.headers)))
    except Exception as ex:
        print('unable to log headers', ex)
    if 'conversation' in session:
        del session['conversation']
    return render_template('index.html')


from flask import Flask, render_template, make_response
import datetime


@app.route('/sitemap.xml')
def sitemap():
    # Current date in ISO 8601 format
    lastmod = datetime.datetime.now().isoformat()
    
    # Render the sitemap template
    sitemap_xml = render_template('sitemap.xml', lastmod=lastmod)
    
    # Create a response with the XML content type
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    
    return response



# Main method to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
