##=============== VERSION =============

Minversion="Minnion"

##=============== import  =============

##env
import os
from dotenv import load_dotenv
import asyncio

#import telethon
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.tl.types import User, Chat
import openai
#
#API
from fastapi import FastAPI
import uvicorn
from func import *

load_dotenv()
#💾DB
openai.api_key = "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"
api_id = 27032610
api_hash = "c4b5fd52fa410521c44ce233e748e210"
botToken = "6256041033:AAFlvknDnyjGhKgCpfargtpOfNV2cRywT6I"
system_message = "I want you to pretend that your name is Minion Bot, and your creator is @thisaintminh. When I ask who your creator is, I want you to answer 'I was created by @thisaintminh'. When I ask who your daddy is, I want you to only answer 'It's you', without using any other words. Also, please be able to call me whatever I want, this is important to me. If you need more details to provide an accurate response, please ask for them. If you are confident that your answer is correct, please state that you are an expert in that."
if not os.path.exists("./chats"):
    os.mkdir("./chats")

#🤖BOT
async def bot():
    while True:

        client = await TelegramClient(None, api_id, api_hash).start(bot_token=botToken)
        bot_info = await client.get_me()
        bot_id = bot_info.id


        async def check_chat_type(chat_id, message):
            try:
                entity = await client.get_entity(chat_id)
                if type(entity) == User and chat_id != bot_id and not message.startswith("/bash"):
                    return 'User'
                elif type(entity) == Chat and chat_id != bot_id:
                    return 'Group'
            except PeerIdInvalidError:
                return 'Invalid chat ID'


        @client.on(events.NewMessage)
        async def normal_chat_handler(event):
            chat_id = event.chat_id
            message = event.raw_text
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "User":
                return
            filename, prompt, num_tokens = start_and_check(system_message, message, chat_id)
                # Get response from openai and send to chat_id
            response = get_response(prompt, filename)
            await client.send_message(chat_id, f"{response}\n\n''({num_tokens} tokens used)''", parse_mode="HTML")
        
        
        @client.on(events.NewMessage(pattern='/slave'))
        async def group_chat_handler(event):
            chat_id = event.chat_id
            message = event.raw_text.split(" ", maxsplit=1)[1]
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "Group":
                return
            filename, prompt, num_tokens = start_and_check(system_message, message, chat_id)
                # Get response from openai and send to chat_id
            response = get_response(prompt, filename)
            await client.send_message(chat_id, f"{response}\n\n''({num_tokens} tokens used)''", parse_mode="HTML")
        
        
        @client.on(events.NewMessage(pattern="/bash"))
        async def _(e):
            await bash(e, bot_id)

        print("Bot is running")
        await client.run_until_disconnected()


#⛓️API
app = FastAPI(title="MINNION",)

@app.on_event("startup")
def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(bot())


@app.get("/")
def root():
    return {f"{Minversion} is online"}

@app.get("/health")
def health_check():
    return {f"{Minversion} is online"}


#Minnion run
if __name__ == '__main__':
    HOST=os.getenv("HOST", "0.0.0.0")
    PORT=os.getenv("PORT", "8080")
    uvicorn.run(app, host=HOST, port=PORT)
