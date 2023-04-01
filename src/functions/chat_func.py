import json
import logging
import os
from typing import List, Tuple

import openai
from src.utils import (
    LOG_PATH,
    SYS_MESS,
    Prompt,
    num_tokens_from_messages,
    read_existing_conversation,
    split_text,
)
from telethon.events import NewMessage


async def over_token(
    num_tokens: int, event: NewMessage, prompt: Prompt, filename: str
) -> None:
    try:
        await event.reply(
            f"**Reach {num_tokens} tokens**, exceeds 4000, creating new chat"
        )
        prompt.append({"role": "user", "content": "summarize this conversation"})
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=prompt
        )
        response = completion.choices[0].message.content
        data = {"messages": SYS_MESS}
        data["messages"].append({"role": "system", "content": response})
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug(f"Successfully handle overtoken")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        await event.reply("An error occurred: {}".format(str(e)))


async def start_and_check(
    event: NewMessage, message: str, chat_id: int
) -> Tuple[str, Prompt]:
    try:
        if not os.path.exists(f"{LOG_PATH}{chat_id}_session.json"):
            data = {"session": 1}
            with open(f"{LOG_PATH}{chat_id}_session.json", "w") as f:
                json.dump(data, f)
        while True:
            file_num, filename, prompt = await read_existing_conversation(chat_id)
            prompt.append({"role": "user", "content": message})
            num_tokens = num_tokens_from_messages(prompt)
            if num_tokens > 4000:
                logging.warn("Number of tokens exceeds 4096 limit")
                file_num += 1
                data = {"session": file_num}
                with open(f"{LOG_PATH}{chat_id}_session.json", "w") as f:
                    json.dump(data, f)
                await over_token(num_tokens, event, prompt, filename)
                continue
            else:
                break
        logging.debug(f"Done start and check")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return filename, prompt


def get_response(prompt: Prompt, filename: str) -> List[str]:
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=prompt
        )
        result = completion.choices[0].message
        num_tokens = completion.usage.total_tokens
        responses = f"{result.content}\n\n__({num_tokens} tokens used)__"
        prompt.append(result)
        data = {"messages": prompt}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug("Received response from openai")
    except Exception as e:
        responses = "💩 OpenAI is being stupid, please try again "
        logging.error(f"Error occurred while getting response from openai: {e}")
    return responses


async def process_and_send_mess(event, text: str, limit=500) -> None:
    text_lst = text.split("```")
    cur_limit = limit
    for idx, text in enumerate(text_lst):
        if idx % 2 == 0:
            await split_text(event, text, cur_limit)
        else:
            await split_text(event, text, cur_limit, "```\n", "\n```")
