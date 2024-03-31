from flask import session, request
from openai import OpenAI
from util import hash_ip
from logger import app_logger
import json
from db import Requests, ThreadComments, Builds, Users, Conversations, Prompts, Translations
from util import get_build_hash, hash_ip

from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI()

conversations_handle = Conversations()
prompts_handle = Prompts()
translations_handle = Translations()


def translate_text(text, target_language='en'):
    completion = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": f"You are a translation to translate into {target_language}. Translate the input to {target_language}."},
            {"role": "user", "content": text}
        ]
    )

    text_response = completion.choices[0].message.content
    translations_handle.insert(hash_ip(), text, text_response, target_language)
    return text_response


def generate_gpt_response(user_input, target_language="spanish"):

    if 'conversation' not in session:
        latest_prompt_row = prompts_handle.get_latest()
        latest_prompt = latest_prompt_row[1]
        prompt_inject_language = latest_prompt.replace("{target_language}", target_language)
        conversations_json_text = json.dumps({
            "data": [{"role": "system", "content": prompt_inject_language}],
            "build": get_build_hash()
        }, indent=2)
        
        conversations_id = conversations_handle.insert(hash_ip(), conversations_json_text)
        session['conversation'] = conversations_id

    conversations_row = conversations_handle.query_by_id(session['conversation'])
    conversations_json_text = conversations_row[-1]
    conversation = json.loads(conversations_json_text)
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
        {"role": "assistant", "content": text_response}
    )
    
    conversations_json_text = json.dumps(conversation)
    conversations_handle.update_by_id(session['conversation'], conversations_json_text)
    
    user_ip = '<ip>'
    try:
        user_ip_raw = request.headers['X-Real-IP']
        user_ip = hash_ip(user_ip_raw)[:6]
    except:
        pass

    app_logger.debug(f'ip:{user_ip} - lang:{target_language} - input: {user_input} - response: {text_response}')
    return text_response, 'empty comment'

def generate_daily_prompt(text):
    completion = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
            {"role": "system", "content": f"You are helping me build a system to teach people new language through conversations. \
                Reply with a topic that would be good for someone learning a new language that are different than what is provided.\
                Respond with 1 topic."},
            {"role": "user", "content": text}
        ]
    )

    text_response = completion.choices[0].message.content
    return text_response