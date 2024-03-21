from flask import Flask, request, jsonify, render_template
import os

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
client = OpenAI()


app = Flask(__name__)

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


def generate_gpt_response(user_input):

    # Generate a response from ChatGPT
    completion_comment = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tool to help someone learn spanish. Point out any grammar errors in the user input or say 'no comment' "},
            {"role": "user", "content": user_input}
        ]
    )

    comment = completion_comment.choices[0].message.content

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a tool to help someone learn spanish. Just respond in spanish and continue the conversation."},
            {"role": "user", "content": user_input}
        ]
    )

    text_response = completion.choices[0].message.content

    return text_response, comment

# Main route for receiving user input and generating responses
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_input = data['input']

    # Append user input to conversation history
    conversation_history.append({'role': 'user', 'message': user_input})

    text_response, comment = generate_gpt_response(user_input)

    # Append ChatGPT's response to conversation history
    conversation_history.append({'role': 'assistant', 'message': text_response})

    # Return the response to the user
    return jsonify({"response": text_response, "english": translate_text(text_response), "comment": comment})

# Main route for receiving user input and generating responses
@app.route('/translate_and_ask', methods=['POST'])
def translate_and_ask():
    data = request.get_json()
    user_input = data['input']

    translated_input = translate_text(user_input, target_language='spanish')
    text_response, comment = generate_gpt_response(translated_input)

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
