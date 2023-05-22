import asyncio
import json
import logging
import os
from typing import List, Tuple

import bardapi
import openai
from EdgeGPT import Chatbot
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
            f"**Reach {num_tokens} tokens**, exceeds 4096, creating new chat"
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
        if not os.path.exists(f"{LOG_PATH}chats/session/{chat_id}.json"):
            data = {"session": 1}
            with open(f"{LOG_PATH}chats/session/{chat_id}.json", "w") as f:
                json.dump(data, f)
        while True:
            file_num, filename, prompt = await read_existing_conversation(chat_id)
            prompt.append({"role": "user", "content": message})
            num_tokens = num_tokens_from_messages(prompt)
            if num_tokens > 4096:  # Cant summarize old chats
                logging.warn("Number of tokens exceeds 4096 limit, creating new chat")
                file_num += 1
                await event.reply(
                    f"**Reach {num_tokens} tokens**, exceeds 4096, clear old chat, creating new chat"
                )
                data = {"session": file_num}
                with open(f"{LOG_PATH}chats/session/{chat_id}.json", "w") as f:
                    json.dump(data, f)
                continue
            elif num_tokens > 4079:  # Summarize old chats
                logging.warn(
                    "Number of tokens nearly exceeds 4096 limit, summarizing old chats"
                )
                file_num += 1
                data = {"session": file_num}
                with open(f"{LOG_PATH}chats/session/{chat_id}.json", "w") as f:
                    json.dump(data, f)
                await over_token(num_tokens, event, prompt, filename)
                continue
            else:
                break
        logging.debug(f"Done start and check")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return filename, prompt


def get_openai_response(prompt: Prompt, filename: str) -> List[str]:
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


def get_bard_response(input_text: str) -> List[str]:
    try:
        if input_text.startswith("/timeout"):
            split_text = input_text.split(maxsplit=2)
            try:
                timeout = int(split_text[1])
            except Exception as e:
                logging.error(f"Incorrect time input: {e}")
                return "Incorrect time input! Correct input should follow: **/bard /timeout {number}**. For example: /bard /timeout 120"
        else:
            timeout = 60
        # Send an API request and get a response.
        responses = bardapi.core.Bard(timeout=timeout).get_answer(input_text)["content"]
        logging.debug("Received response from bard")
    except Exception as e:
        responses = "💩 Bard is being stupid, please try again "
        logging.error(f"Error occurred while getting response from bard: {e}")
    return responses


def get_bing_response(input_text):
    try:
        COOKIE_PATH = os.getenv("COOKIE_PATH")
        response_dict = asyncio.run(
            Chatbot(cookie_path=f"{COOKIE_PATH}cookies.json").ask(
                prompt=input_text, conversation_style="creative"
            )
        )
        responses = response_dict["item"]["messages"][1]["text"]
        suggest_lst = [
            x["text"]
            for x in response_dict["item"]["messages"][1]["suggestedResponses"]
        ]
        logging.debug("Received response from bing")
    except Exception as e:
        responses = "💩 Bing is being stupid, please try again "
        suggest_lst = []
        logging.error(f"Error occurred while getting response from bing: {e}")
    return responses, suggest_lst


async def process_and_send_mess(event, text: str, limit=500) -> None:
    text_lst = text.split("```")
    cur_limit = 4096
    for idx, text in enumerate(text_lst):
        if idx % 2 == 0:
            mess_gen = split_text(text, cur_limit)
            for mess in mess_gen:
                await event.client.send_message(
                    event.chat_id, mess, background=True, silent=True
                )
                await asyncio.sleep(1)
        else:
            mess_gen = split_text(text, cur_limit, prefix="```\n", sulfix="\n```")
            for mess in mess_gen:
                await event.client.send_message(
                    event.chat_id, mess, background=True, silent=True
                )
                await asyncio.sleep(1)
