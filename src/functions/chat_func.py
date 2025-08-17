import asyncio
import json
import logging
import os
from typing import List, Tuple

import bardapi
import google.generativeai as genai
import openai
import PIL.Image
from bardapi import Bard
from EdgeGPT.EdgeUtils import Query
from openai.error import APIConnectionError
from telethon.events import NewMessage

import src.utils
from src.utils import (
    LOG_PATH,
    Prompt,
    num_tokens_from_messages,
    read_existing_conversation,
    split_text,
)


async def over_token(
    num_tokens: int, event: NewMessage, prompt: Prompt, filename: str
) -> None:
    MAX_TOKEN = src.utils.utils.max_token
    SYS_MESS = src.utils.utils.sys_mess
    MODEL = src.utils.utils.model
    try:
        await event.reply(
            f"**Reach {num_tokens} tokens**, exceeds {MAX_TOKEN}, creating new chat"
        )
        prompt.append({"role": "user", "content": "summarize this conversation"})
        completion = openai.ChatCompletion.create(model=MODEL, messages=prompt)
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
    MAX_TOKEN = src.utils.utils.max_token
    try:
        if not os.path.exists(f"{LOG_PATH}chats/session/{chat_id}.json"):
            data = {"session": 1}
            with open(f"{LOG_PATH}chats/session/{chat_id}.json", "w") as f:
                json.dump(data, f)
        while True:
            file_num, filename, prompt = await read_existing_conversation(chat_id)
            prompt.append({"role": "user", "content": message})
            num_tokens = num_tokens_from_messages(prompt)
            if num_tokens > MAX_TOKEN:  # Cant summarize old chats
                logging.warn(
                    f"Number of tokens exceeds {MAX_TOKEN} limit, creating new chat"
                )
                file_num += 1
                await event.reply(
                    f"**Reach {num_tokens} tokens**, exceeds {MAX_TOKEN}, clear old chat, creating new chat"
                )
                data = {"session": file_num}
                with open(f"{LOG_PATH}chats/session/{chat_id}.json", "w") as f:
                    json.dump(data, f)
                continue
            elif num_tokens > MAX_TOKEN - 17:  # Summarize old chats
                logging.warn(
                    f"Number of tokens nearly exceeds {MAX_TOKEN} limit, summarizing old chats"
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


def get_openai_response(prompt: Prompt, filename: str) -> str:
    MAX_TOKEN = src.utils.utils.max_token
    MODEL = src.utils.utils.model
    trial = 0
    while trial < 5:
        try:
            completion = openai.ChatCompletion.create(model=MODEL, messages=prompt)
            result = completion.choices[0].message
            num_tokens_left = MAX_TOKEN - completion.usage.total_tokens
            responses = f"{result.content}\n\n__({num_tokens_left} tokens left)__"
            prompt.append(result)
            data = {"messages": prompt}
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            logging.debug("Received response from openai")
            trial = 5
        except APIConnectionError:
            responses = "🔌 Render and OpenAI hate each other"
            logging.error(f"API Connection failed: {e}")
            trial += 1
        except Exception as e:
            responses = "💩 OpenAI is being stupid, please try again "
            logging.error(f"Error occurred while getting response from openai: {e}")
            trial += 1
    return responses


def get_bard_response(input_text: str) -> str:
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
        try:
            responses = Bard(token_from_browser=True).get_answer(input_text)
            logging.debug("Received response from bard by token_from_browser")
        except:
            # Send an API request and get a response.
            responses = bardapi.core.Bard(timeout=timeout).get_answer(input_text)[
                "content"
            ]
            logging.debug("Received response from bard by token")
    except Exception as e:
        responses = "🤯 Bard is under construction, dont use it for now "
        logging.error(f"Error occurred while getting response from bard: {e}")
    return responses


def get_gemini_response(input_text: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            input_text,
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ],
        )
        responses = response.text
    except Exception as e:
        responses = "💩 Gemini is being stupid, please try again "
        logging.error(f"Error occurred while getting response from gemini: {e}")
    return responses


def get_gemini_vison_response(input_text: str, img_path: str) -> str:
    try:
        img = PIL.Image.open(img_path)
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                [
                    input_text,
                    img,
                ],
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ],
            )
            response.resolve()
            responses = response.text
        except Exception as e:
            responses = "💩 Gemini Vision is being stupid, please try again "
            logging.error(f"Error occurred while getting response from gemini: {e}")
    except Exception as e:
        responses = "💩 Something wrong with processing the media"
        logging.error(f"Error occurred while processing the media: {e}")
    return responses


def get_bing_response(input_text):
    try:
        COOKIE_PATH = os.getenv("COOKIE_PATH")
        q = Query(
            input_text,
            style="creative",  # or: 'balanced', 'precise'
            cookie_file=COOKIE_PATH,
        )
        responses = []
        source_lst = []
        messages = q.response["item"]["messages"]
        for response_dict in messages:
            if response_dict["author"] == "bot" and "text" in response_dict:
                responses.append(response_dict["text"])
                if "sourceAttributions" in response_dict:
                    source_lst = [
                        x["seeMoreUrl"] for x in response_dict["sourceAttributions"]
                    ]

        # TODO: replace sending suggest list by sources
        suggest_lst = [
            x["text"]
            for x in response_dict["item"]["messages"][1]["suggestedResponses"]
        ]
        logging.debug("Received response from bing")
    except Exception as e:
        responses = "🤯 Bing is under construction, dont use it for now "
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
