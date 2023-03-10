from telethon import TelegramClient, events
import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.environ.get('API_KEY')
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
botToken = os.environ.get('BOTTOKEN')

client = TelegramClient('minnion-render', api_id, api_hash)
client.start(bot_token=botToken)
if not os.path.exists("./chats"):
    os.mkdir("./chats")



@client.on(events.NewMessage)
async def event_handler(event):
    user = event.sender_id
    message = event.raw_text
    if not os.path.exists(f"{user}_session.json"):
      data = {"session": 1}
      with open(f"{user}_session.json", 'w') as f:
          json.dump(data, f)
    filename, prompt, num_tokens = start_and_check(message, user)
        # Get response from openai and send to user
    respose = get_response(prompt, filename)
    await event.respond(f"{respose}\n\n(used {num_tokens} tokens)")

def start_and_check(message, user):
    while True:
        with open(f"{user}_session.json", 'r') as f:
          file_num=json.load(f)['session']
        filename = f'chats/{user}_{file_num}.json'
            # Create .json file in case of new chat
        if not os.path.exists(filename):
            data = {
                    "messages": [{
                                "role": "system",
                                "content": "You are a large AI language model. you know everything. Your job is to provide solutions / suggestion to problems. Your name is Minnion. If found mistakes in English of question, rewrite it before giving responses. Ask for more details if needed. You were created by @thisaintminh."
                                }],
                    "num_tokens": 0
                    }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        with open(filename, 'r') as f:
            data = json.load(f)
        prompt = []
        for item in data['messages']:
            prompt.append(item)
            
        num_tokens=data["num_tokens"]
        if num_tokens > 4000:
            file_num += 1
            data = {"session": file_num}
            with open(f"{user}_session.json", 'w') as f:
                json.dump(data, f)
            client.send_message('thisaintminh', f"{num_tokens} exceeds 4096, creating new chat")
            prompt.append({
                "role": "user",
                "content": "summarize this conversation"
            })
            completion = openai.ChatCompletion.create(
                                                        model='gpt-3.5-turbo',
                                                        messages=prompt
                                                    )
            response = completion.choices[0].message.content
            num_tokens = completion.usage.total_tokens
            data = {
                "messages": [{
                            "role": "system",
                            "content": "You are a large AI language model. you know everything. Your job is to provide solutions / suggestion to problems. Your name is Minnion. If found mistakes in English of question, rewrite it before giving responses. Ask for more details if needed. You were created by @thisaintminh."
                            },
                            {
                            "role": "system",
                            "content": response
                            }],
                "num_tokens": num_tokens
                    }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            continue
        else: break

    prompt.append({
                    "role": "user",
                    "content": message
                }) 
    return filename, prompt


def get_response(prompt, filename):
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=prompt
    )
    response = completion.choices[0].message.content
    num_tokens = completion.usage.total_tokens
    prompt.append(
        {
            "role": "assistant",
            "content": response
        })
    data= {"messages":prompt, "num_tokens":num_tokens}
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    return response

bot.run_until_disconnected()
