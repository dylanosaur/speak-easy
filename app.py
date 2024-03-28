from flask import Flask, request, jsonify, render_template, session, make_response
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
import json
from ai_generator import openai_client, translate_text, generate_gpt_response
from bot_comments import bot_comments
from logger import app_logger, headers_logger
from util import hash_ip, build_hash
from db import Requests, ThreadComments, create_table, DB_FILE


requests_handle = Requests()
thread_comments_handle = ThreadComments()
create_table()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

app.register_blueprint(bot_comments)

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
        requests_handle.log_user(ip_address, build_hash)
        return func(*args, **kwargs)
    return wrapper

@app.route('/activity')
def admin():
    results = requests_handle.get_logged_results()
    return render_template('activity.html', results=results)

# Main route for receiving user input and generating responses
@app.route('/ask', methods=['POST'])
@log_request
def ask():

    target_language =  request.args.get('lang', 'spanish')
    data = request.get_json()
    user_input = data['input']

    text_response, comment = generate_gpt_response(user_input, target_language=target_language)

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


@app.route('/', methods=['GET'])
def index():
    try:
        headers_logger.debug(json.dumps(dict(request.headers)))
    except Exception as ex:
        print('unable to log headers', ex)
    if 'conversation' in session:
        del session['conversation']
    return render_template('index.html')


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

@app.route('/plot_activity')
def plot_activity():
    # Calculate average and standard deviation for each buildhash
    data = requests_handle.get_build_and_count()
    print(data)
    data = [{'buildhash': x[0], 'count':x[1], 'index': 0} for x in data]
    current_hash = data[0]['buildhash']
    current_index = 0
    for item in data:
        if item['buildhash'] != current_hash:
            current_index += 1
            current_hash = item['buildhash']
        item['index'] = current_index
        
    index_by_buildhash = {x['buildhash']: x['index'] for x in data}

    buildhashes = list(set([d['buildhash'] for d in data]))
    buildhashes.sort(key=lambda x:index_by_buildhash[x])
    averages = []
    std_devs = []
    for buildhash in buildhashes:
        counts = [d['count'] for d in data if d['buildhash'] == buildhash]
        averages.append(np.mean(counts))
        std_devs.append(np.std(counts))

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(buildhashes)), averages, yerr=std_devs, align='center', alpha=0.5, ecolor='black', capsize=10)
    plt.xticks(range(len(buildhashes)), buildhashes)
    plt.xlabel('Build Hash')
    plt.ylabel('Average Count')
    plt.title('Average Count and Standard Deviation for Each Build Hash')
    plt.tight_layout()

    # Save the plot to a temporary file
    plot_path = 'static/plot.png'
    plt.savefig(plot_path)

    # Render the template with the plot
    return render_template('plot.html', plot_path=plot_path)

if __name__ == '__main__':
    app.run(debug=True)
