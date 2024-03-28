from flask import session, request
from openai import OpenAI
from util import hash_ip
from logger import app_logger

from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI()


def translate_text(text, target_language='en'):
    completion = openai_client.chat.completions.create(
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
                Use beginner-intermediate level words and phrases and limit your response to one sentence and then one question. \
                If they dont ask a question then go ahead and pick some random topic and ask them a question.\
                Dont ask them how you can help, just pick an interesting topic and try to engage them in conversation."},
            ]
        })

    conversation = json.loads(session['conversation'])
    conversation['data'].append(
        {"role": "user", "content": user_input}
    )

    print('generating response using', target_language)

    completion = openai_client.chat.completions.create(
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