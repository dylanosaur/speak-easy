from flask import Flask, request, jsonify, render_template
import os

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
client = OpenAI()



import logging
from datetime import datetime

def create_custom_logger(filename):
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a file handler
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger

app_logger = create_custom_logger('app.log')

app = Flask(__name__)


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
                 (ip TEXT PRIMARY KEY, count INTEGER)''')
    conn.commit()
    conn.close()

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
            c.execute("INSERT INTO requests VALUES (?, 1)", (ip_address,))
        
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


def generate_gpt_response(user_input, target_language="spanish"):

    print('generating response using', target_language)
    # Generate a response from ChatGPT
    completion_comment = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a tool to help someone learn {target_language}. Point out any grammar errors in the user input or say 'no comment' "},
            {"role": "user", "content": user_input}
        ]
    )

    comment = completion_comment.choices[0].message.content

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a tool to help someone learn {target_language}. \
                Just respond in {target_language} and continue the conversation. \
                Use beginner-intermediate level words and phrases and limit your response to one sentence and then one question"},
            {"role": "user", "content": user_input}
        ]
    )

    text_response = completion.choices[0].message.content

    app_logger.debug(f'lang {target_language} user input {user_input} has response {text_response}')
    return text_response, comment


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
    return render_template('index.html')

# Main method to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
