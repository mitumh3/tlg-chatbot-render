import io
import logging
import os
import subprocess

import openai
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from telethon import TelegramClient, functions
from telethon.errors.rpcerrorlist import UnauthorizedError

from __version__ import __version__
from handlers import *
from src import *

try:
    Minversion = f"Minnion {__version__}"
except:
    Minversion = "Minnion v1.0.0"
# Load the logging configuration file
logging.config.fileConfig("log/logging.ini")
# Set the log level to INFO
logging.getLogger("appLogger")
# Create a StringIO object to capture log messages sent to the console
console_out = io.StringIO()
# Set the stream of the console handler to the StringIO object
console_handler = logging.getLogger("appLogger").handlers[0]
console_handler.stream = console_out

# Load  keys
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
botToken = os.getenv("BOTTOKEN")

if not os.path.exists("./log/chats"):
    os.mkdir("./log/chats")


# Bot func
async def bot() -> None:
    while True:
        try:
            client = await TelegramClient(None, api_id, api_hash).start(bot_token=botToken)
            bot_info = await client.get_me()
            bot_id = bot_info.id
            logging.info("Successfully initiate bot")
            await client(functions.contacts.BlockRequest(id=bot_id))
        except UnauthorizedError:
            logging.error("Unauthorized access. Please check your Telethon API ID, API hash")
        except Exception as e:
            logging.error(f"Error occurred: {e}")

        # Search feature
        client.add_event_handler(search_handler)
        # Terminal bash feature
        client.add_event_handler(bash_handler)
        # Clear chat history feature
        client.add_event_handler(clear_handler)
        # User and group chat
        client.add_event_handler(user_chat_handler)
        client.add_event_handler(group_chat_handler)

        print("Bot is running")
        await client.run_until_disconnected()


# API and app handling
app = FastAPI(
    title="MINNION",
)


@app.on_event("startup")
def startup_event() -> None:
    try:
        loop = asyncio.get_event_loop()
        background_tasks = set()
        task = loop.create_task(bot())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    except Exception as e:
        logging.critical(f"Error occurred while starting up app: {e}")


@app.get("/")
def root() -> str:
    return {f"{Minversion} is online"}


@app.get("/health")
def health_check() -> str:
    return {f"{Minversion} is online"}


@app.get("/log")
async def log_check() -> StreamingResponse:
    async def generate_log() -> Generator[bytes, None, None]:
        console_log = console_out.getvalue()
        yield f"{console_log}".encode("utf-8")

    return StreamingResponse(generate_log())


@app.get("/terminal", response_class=HTMLResponse)
async def terminal(request: Request) -> Response:
    return Response(content=terminal_html(), media_type="text/html")


@app.post("/terminal/run")
async def run_command(command: dict) -> str:
    try:
        output_bytes = subprocess.check_output(command["command"], shell=True, stderr=subprocess.STDOUT)
        output_str = output_bytes.decode("utf-8")
        # Split output into lines and remove any leading/trailing whitespace
        output_lines = [line.strip() for line in output_str.split("\n")]
        # Join lines with a <br> tag for display in HTML
        formatted_output = "<br>".join(output_lines)
    except subprocess.CalledProcessError as e:
        formatted_output = e.output.decode("utf-8")
    return formatted_output


# Minnion run
if __name__ == "__main__":
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 8080)
    uvicorn.run(app, host=HOST, port=PORT)
