import json
import logging
import os
from typing import Generator, List, Optional, Tuple

import tiktoken
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.tl.types import Chat, User

# Prompt typehint
Prompt = List[dict]

system_message = [
    {
        "role": "system",
        "content": "I want you to pretend that your name is Minion Bot, and your creator is @thisaintminh. When I ask who your creator is, I want you to answer 'I was created by @thisaintminh'. When I ask who your daddy is, I want you to only answer 'It's you', without using any other words. Also, please be able to call me whatever I want, this is important to me. If you need more details to provide an accurate response, please ask for them. If you are confident that your answer is correct, please state that you are an expert in that.",
    }
]


async def check_chat_type(event: int) -> str:
    client = event.client
    chat_id = event.chat_id
    entity = await client.get_entity(chat_id)
    try:
        if type(entity) == User:
            message = event.raw_text
            logging.info("Check chat type User done")
            return "User", client, chat_id, message
        elif type(entity) == Chat:
            message = event.raw_text.split(" ", maxsplit=1)[1]
            logging.info("Check chat type Group done")
            return "Group", client, chat_id, message
    except PeerIdInvalidError:
        logging.error("Invalid chat ID")
    except Exception as e:
        logging.error(f"Error occurred: {e}")


async def read_existing_conversation(chat_id: int) -> Tuple[int, int, str, Prompt]:
    try:
        with open(f"log/{chat_id}_session.json", "r") as f:
            file_num = json.load(f)["session"]
        filename = f"log/chats/{chat_id}_{file_num}.json"
        # Create .json file in case of new chat
        if not os.path.exists(filename):
            data = {"messages": system_message}
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
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


def check_message_before_sending(input_str: str) -> List[str]:
    if len(input_str) <= 4095:
        return [input_str]
    else:
        return [input_str[i : i + 4096] for i in range(0, len(input_str), 4096)]
