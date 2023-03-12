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
openai.api_key = os.getenv("OPENAI_API_KEY")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
botToken = os.getenv("BOTTOKEN")

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
                if type(entity) == User and chat_id != bot_id and not message.startswith("/bash") and not message.startswith("/search"):
                    return 'User'
                elif type(entity) == Chat and chat_id != bot_id:
                    return 'Group'
            except PeerIdInvalidError:
                return 'Invalid chat ID'


        @client.on(events.NewMessage)
        async def normal_chat_handler(e):
            chat_id = e.chat_id
            message = e.raw_text
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "User":
                return
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(1)
                filename, prompt, num_tokens = start_and_check(e, message, chat_id)
                    # Get response from openai and send to chat_id
                response = get_response(prompt, filename)
                await client.send_message(chat_id, f"{response}\n\n__({num_tokens} tokens used)__")
            await client.action(chat_id, 'cancel')
        
        @client.on(events.NewMessage(pattern='/slave'))
        async def group_chat_handler(e):
            chat_id = e.chat_id
            message = e.raw_text.split(" ", maxsplit=1)[1]
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "Group":
                return
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(1)
                filename, prompt, num_tokens = start_and_check(e, message, chat_id)
                    # Get response from openai and send to chat_id
                response = get_response(prompt, filename)
                await client.send_message(chat_id, f"{response}\n\n__({num_tokens} tokens used)__")
            await client.action(chat_id, 'cancel')
        
        @client.on(events.NewMessage(pattern="/search"))
        async def _(e):
            chat_id = e.chat_id
            async with client.action(chat_id, 'typing'):
                await asyncio.sleep(1)
                response = search(e, bot_id)
                await client.send_message(chat_id, f"__Here is your search:__\n{response}")
            await client.action(chat_id, 'cancel')

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
