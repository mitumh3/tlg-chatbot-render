import io
import logging
import subprocess

import openai
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import PeerIdInvalidError, UnauthorizedError
from telethon.tl.types import Chat, User

from func import *

Minversion = "Minnion"


# Load the logging configuration file
logging.config.fileConfig("logging.ini")
# Set the log level to INFO
logging.getLogger("appLogger")
# Create a StringIO object to capture log messages sent to the console
console_out = io.StringIO()
# Set the stream of the console handler to the StringIO object
console_handler = logging.getLogger("appLogger").handlers[0]
console_handler.stream = console_out

# 💾DB
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
botToken = os.getenv("BOTTOKEN")

if not os.path.exists("./chats"):
    os.mkdir("./chats")


# 🤖BOT
async def bot():
    while True:
        try:
            client = await TelegramClient(None, api_id, api_hash).start(bot_token=botToken)
            bot_info = await client.get_me()
            bot_id = bot_info.id
            logging.info("Successfully initiate bot")
        except UnauthorizedError:
            logging.error("Unauthorized access. Please check your Telethon API ID, API hash")
        except Exception as e:
            logging.error(f"Error occurred: {e}")

        async def check_chat_type(chat_id, message):
            try:
                entity = await client.get_entity(chat_id)
                if (
                    type(entity) == User
                    and chat_id != bot_id
                    and not message.startswith("/bash")
                    and not message.startswith("/search")
                ):
                    return "User"
                elif type(entity) == Chat and chat_id != bot_id:
                    return "Group"
                logging.info("Check chat type done")
            except PeerIdInvalidError:
                logging.error("Invalid chat ID")
            except Exception as e:
                logging.error(f"Error occurred: {e}")

        @client.on(events.NewMessage)
        async def normal_chat_handler(e):
            chat_id = e.chat_id
            message = e.raw_text
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "User":
                return
            async with client.action(chat_id, "typing"):
                await asyncio.sleep(0.5)
                filename, prompt, num_tokens = await start_and_check(e, message, chat_id)
                # Get response from openai and send to chat_id
                response = await get_response(prompt, filename)
                try:
                    await client.send_message(chat_id, f"{response}\n\n__({num_tokens} tokens used)__")
                    logging.info(f"Sent message to {chat_id}")
                except Exception as e:
                    logging.error(f"Error occurred: {e}")
            await client.action(chat_id, "cancel")

        @client.on(events.NewMessage(pattern="/slave"))
        async def group_chat_handler(e):
            chat_id = e.chat_id
            message = e.raw_text.split(" ", maxsplit=1)[1]
            chat_type = await check_chat_type(chat_id, message)
            if chat_type != "Group":
                return
            async with client.action(chat_id, "typing"):
                await asyncio.sleep(0.5)
                filename, prompt, num_tokens = await start_and_check(e, message, chat_id)
                # Get response from openai and send to chat_id
                response = await get_response(prompt, filename)
                try:
                    await client.send_message(chat_id, f"{response}\n\n__({num_tokens} tokens used)__")
                    logging.info(f"Sent message to {chat_id}")
                except Exception as e:
                    logging.error(f"Error occurred: {e}")
            await client.action(chat_id, "cancel")

        @client.on(events.NewMessage(pattern="/search"))
        async def _(e):
            chat_id = e.chat_id
            async with client.action(chat_id, "typing"):
                await asyncio.sleep(0.5)
                response = await search(e, bot_id)
                try:
                    await client.send_message(chat_id, f"__Here is your search:__\n{response}")
                    logging.info(f"Sent /search to {chat_id}")
                except Exception as e:
                    logging.error(f"Error occurred: {e}")
            await client.action(chat_id, "cancel")

        @client.on(events.NewMessage(pattern="/bash"))
        async def _(e):
            response = await bash(e, bot_id)
            try:
                await client.send_message(e.chat_id, f"{response}")
                logging.info(f"Sent /bash to {e.chat_id}")
            except Exception as e:
                logging.error(f"Error occurred while responding /bash cmd: {e}")

        print("Bot is running")
        await client.run_until_disconnected()


# ⛓️API
app = FastAPI(
    title="MINNION",
)


@app.on_event("startup")
def startup_event():
    try:
        loop = asyncio.get_event_loop()
        background_tasks = set()
        task = loop.create_task(bot())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    except Exception as e:
        logging.critical(f"Error occurred while starting up app: {e}")


@app.get("/")
def root():
    return {f"{Minversion} is online"}


@app.get("/health")
def health_check():
    return {f"{Minversion} is online"}


@app.get("/log")
async def log_check(response: Response):
    async def generate_log():
        console_log = console_out.getvalue()
        yield f"<pre>{console_log}</pre>".encode("utf-8")

    return StreamingResponse(generate_log())


@app.get("/terminal", response_class=HTMLResponse)
async def terminal(request: Request):
    return """
    <html>
    <head>
        <title>Terminal</title>
        <script>
            function sendCommand() {
                const command = document.getElementById("command").value;
                fetch("/terminal/run", {
                    method: "POST",
                    body: JSON.stringify({command: command}),
                    headers: {
                        "Content-Type": "application/json"
                    }
                })
                .then(response => response.text())
                .then(data => {
                    document.getElementById("output").innerHTML += data + "<br>";
                });
                document.getElementById("command").value = "";
            }
        </script>
    </head>
    <body>
        <div id="output"></div>
        <input type="text" id="command" onkeydown="if (event.keyCode == 13) sendCommand()">
        <button onclick="sendCommand()">Run</button>
    </body>
    </html>
    """


@app.post("/terminal/run")
async def run_command(command: dict):
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
