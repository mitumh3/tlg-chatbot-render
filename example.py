##=============== VERSION =============

Minversion="Minnion"

##=============== import  =============

##env
import os
from dotenv import load_dotenv
import json
import asyncio

#import telethon
from telethon import TelegramClient, events
import openai
#
#API
from fastapi import FastAPI, Request
import uvicorn
#Utils

#🔧CONFIG
load_dotenv()


#🔁UTILS
"""
🔚END OF COMMON FUNCTIONS
"""
#💾DB
openai.api_key = "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"
api_id = 27032610
api_hash = "c4b5fd52fa410521c44ce233e748e210"
botToken = "6256041033:AAFlvknDnyjGhKgCpfargtpOfNV2cRywT6I"
if not os.path.exists("./chats"):
    os.mkdir("./chats")

#🤖BOT
async def bot():
    while True:
#StartTheBot
        bot = await TelegramClient(None, api_id, api_hash).start(bot_token=botToken)
        bot_info = await bot.get_me()
        bot_id = bot_info.id
        @bot.on(events.NewMessage)
        async def event_handler(event):
            user = event.sender_id
            message = event.raw_text
            if user != bot_id:
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
                        bot.send_message('thisaintminh', f"{num_tokens} exceeds 4096, creating new chat")
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
                return filename, prompt, num_tokens


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

        await bot.run_until_disconnected()

#⛓️API
app = FastAPI(title="MINNION",)

@app.on_event("startup")
def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(bot())


@app.get("/")
def root():
    return {f"Bot is online {Minversion}"}

@app.get("/health")
def health_check():
    return {f"Bot is online {Minversion}"}


#Minnion run
if __name__ == '__main__':
    HOST=os.getenv("HOST", "0.0.0.0")
    PORT=os.getenv("PORT", "8080")
    uvicorn.run(app, host=HOST, port=PORT)
