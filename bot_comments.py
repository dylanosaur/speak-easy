from db import Requests, ThreadComments, create_table, DB_FILE
requests_handle = Requests()
thread_comments_handle = ThreadComments()

from flask import Blueprint, request,jsonify, render_template
from ai_generator import openai_client

bot_comments = Blueprint('bot_comments', __name__)

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
        
    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    text_response = completion.choices[0].message.content

    text_response = text_response.replace("!", ".").replace("SpeakEZ", "https://speak-ez.net").replace('"', '').replace("'", "")

    return text_response


# Main route for receiving user input and generating responses
@bot_comments.route('/reddit_response', methods=['POST'])
def reddit_response():
    data = request.get_json()
    user_input = data['input']
    url = data['url']

    url_already_processed = thread_comments_handle.check_url_existence(url)
    if url_already_processed:
        print('url has already been processed', url)
        text_response = None
    else:
        comment_count = thread_comments_handle.count_comments()
        recommend_enabled = comment_count % 30 == 0
        print('recommend is enabled', recommend_enabled, comment_count)
        text_response = generate_gpt_response_reddit_comment(user_input, recommend_speak_easy=recommend_enabled)

        thread_comments_handle.insert_comment(url, user_input, text_response)

    # Return the response to the user
    return jsonify({"response": text_response})

@bot_comments.route('/reddit_response_success', methods=['POST'])
def reddit_response_success():
    data = request.get_json()
    url = data['url']

    ThreadComments.mark_url_as_success(url)
    return jsonify({"data": "success"})

# Route to display the ThreadComments in a table
@bot_comments.route('/thread_comments')
def show_comments():
    # Connect to the SQLite database
    comments = thread_comments_handle.get_all()

    # Render the HTML template with comments data
    return render_template('comments.html', comments=comments)