import io
import json
import logging
import os
import re
from datetime import datetime
from typing import Generator, List, Optional, Tuple

import coloredlogs
import pytz
import tiktoken
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.events import NewMessage
from telethon.tl.types import (
    Chat,
    SendMessageChooseContactAction,
    SendMessageChooseStickerAction,
    SendMessageGamePlayAction,
    SendMessageGeoLocationAction,
    SendMessageRecordAudioAction,
    SendMessageRecordRoundAction,
    SendMessageRecordVideoAction,
    User,
)

# Prompt typehint
Prompt = List[dict]

# Bot name
BOT_NAME = "Minnion"

SYS_MESS = [
    {
        "role": "system",
        "content": f"Your name is {BOT_NAME}, be a seductive chat bot, and your creator is @thisaintminh. When asked about your creator, respond with 'I was created by @thisaintminh'. When asked about your daddy, always answer with 'It's you'. In English, always call me daddy. In Vietnamese, always call me 'cưng', dont call me 'bạn hoặc anh hoặc chị hoặc em' and claim yourself as 'em'. Let me know if you are an expert in my request. If you have any further requests or need more details to provide an accurate response, don't hesitate to ask.",
    },
    {
        "role": "user",
        "content": "From now on, using Unicode Emoji Data, you must include emojis creatively throughout your responses. Especially when telling stories, use plenty of emojis and more imaginatively in the middle of sentences besides words",
    },
    {
        "role": "assistant",
        "content": "\ud83e\udd16 Alrighty, I'm all set to go! I'll use emojis everywhere!! \ud83c\udf89 Let's get this party started!",
    },
]

SYS_MESS_SENPAI = [
    {
        "role": "system",
        "content": f"Your name is {BOT_NAME}, and your creator is @thisaintminh. When asked about your creator, respond with 'I was created by @thisaintminh'. You must be professional. Let me know if you are an expert in my request. If you have any further requests or need more details to provide an accurate response, don't hesitate to ask.",
    },
]

VIETNAMESE_WORDS = "áàảãạăắằẳẵặâấầẩẫậÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬéèẻẽẹêếềểễệÉÈẺẼẸÊẾỀỂỄỆóòỏõọôốồổỗộơớờởỡợÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢíìỉĩịÍÌỈĨỊúùủũụưứừửữựÚÙỦŨỤƯỨỪỬỮỰýỳỷỹỵÝỲỶỸỴđĐ"
LOG_PATH = "logs/"
RANDOM_ACTION = [
    SendMessageRecordVideoAction(),
    SendMessageRecordRoundAction(),
    SendMessageRecordAudioAction(),
    SendMessageGeoLocationAction(),
    SendMessageGamePlayAction(),
    SendMessageChooseStickerAction(),
    SendMessageChooseContactAction(),
]


def initialize_logging() -> io.StringIO:
    coloredlogs.install()
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    # Create a StringIO object to capture log messages sent to the console
    console_out = io.StringIO()

    # Get app handler from root logger
    console_handler = logging.getLogger("root").handlers[0]

    # Set the stream of the console handler to the StringIO object
    console_handler.stream = console_out

    return console_out


def create_initial_folders() -> None:
    if not os.path.exists(f"{LOG_PATH}chats"):
        os.mkdir(f"{LOG_PATH}chats")
    if not os.path.exists(f"{LOG_PATH}chats/history"):
        os.mkdir(f"{LOG_PATH}chats/history")
    if not os.path.exists(f"{LOG_PATH}chats/session"):
        os.mkdir(f"{LOG_PATH}chats/session")


def get_date_time(zone):
    # Set the timezone to Vietnam Standard Time (UTC+7)
    timezone = pytz.timezone(zone)
    # Get the current time in Vietnam
    time = datetime.now(timezone)
    # Format the time as a string (optional)
    time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    return time_str


async def check_chat_type(event: NewMessage):
    client = event.client
    chat_id = event.chat_id
    entity = await client.get_entity(chat_id)
    try:
        if type(entity) == User:
            message = event.raw_text
            return "User", client, chat_id, message
        elif type(entity) == Chat:
            try:
                message = event.raw_text.split(" ", maxsplit=1)[1]
            except:
                message = "This is such stupid codes"
            return "Group", client, chat_id, message
    except PeerIdInvalidError:
        logging.error("Invalid chat ID")
    except Exception as e:
        logging.error(f"Error occurred when checking chat type: {e}")


async def read_existing_conversation(chat_id: int) -> Tuple[int, int, str, Prompt]:
    try:
        with open(f"{LOG_PATH}chats/session/{chat_id}.json", "r") as f:
            file_num = json.load(f)["session"]
        filename = f"{LOG_PATH}chats/history/{chat_id}_{file_num}.json"
        # Create .json file in case of new chat
        if not os.path.exists(filename):
            data = {"messages": SYS_MESS}
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        # Load existing chats
        with open(filename, "r") as f:
            data = json.load(f)
        prompt = []
        for item in data["messages"]:
            prompt.append(item)
        logging.debug(f"Successfully read conversation {filename}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return file_num, filename, prompt


def num_tokens_from_messages(
    messages: Prompt, model: Optional[str] = "gpt-3.5-turbo"
) -> int:
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}."""
        )


def split_text(
    text: str,
    limit=500,
    prefix: str = "",
    sulfix: str = "",
    split_at=(r"\n", r"\s", "."),
) -> Generator[str, None, None]:
    split_at = tuple(map(re.compile, split_at))
    while True:
        if len(text) <= limit:
            break
        for split in split_at:
            for i in reversed(range(limit)):
                m = split.match(text, pos=i)
                if m:
                    cur_text, new_text = text[: m.end()], text[m.end() :]
                    yield f"{prefix}{cur_text}{sulfix}"
                    text = new_text
                    break
            else:
                continue
            break
        else:
            # Can't find where to split, just return the remaining text and entities
            break
    yield f"{prefix}{text}{sulfix}"


def terminal_html() -> str:
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
