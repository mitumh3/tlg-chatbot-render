import asyncio
import io
import logging
import os
import subprocess
from typing import Generator

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from meta.__version__ import __version__
from src.bot import *
from src.utils import LOG_PATH, terminal_html

# Load the logging configuration file
logging.config.fileConfig(f"{LOG_PATH}logging.ini")
# Set the log level to INFO
logging.getLogger("appLogger")
# Create a StringIO object to capture log messages sent to the console
console_out = io.StringIO()
# Set the stream of the console handler to the StringIO object
console_handler = logging.getLogger("appLogger").handlers[0]
console_handler.stream = console_out

# Bot name
BOT_NAME = "MINNION"
# Bot version
try:
    BOT_VERSION = __version__
except:
    BOT_VERSION = "v1.0.0"

# API and app handling
app = FastAPI(
    title=BOT_NAME,
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
    return {f"{BOT_NAME} {BOT_VERSION} is online"}


@app.get("/health")
def health_check() -> str:
    return {f"{BOT_NAME} {BOT_VERSION} is online"}


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
        output_bytes = subprocess.check_output(
            command["command"], shell=True, stderr=subprocess.STDOUT
        )
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
