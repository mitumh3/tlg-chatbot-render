import logging
import os
from typing import Tuple

import google.generativeai as genai
import openai
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import UnauthorizedError

from src.handlers import (
    bard_chat_handler,
    bash_handler,
    bing_chat_handler,
    clear_handler,
    gemini_chat_handler,
    group_chat_handler,
    search_handler,
    security_check,
    senpai_chat_handler,
    switch_model_handler,
    user_chat_handler,
)


# Load  keys
def load_keys() -> Tuple[str, int, str]:
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.organization = os.getenv("OPENAI_ORG")
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    bot_token = os.getenv("BOTTOKEN")
    return api_id, api_hash, bot_token


async def bot() -> None:
    while True:
        api_id, api_hash, bot_token = load_keys()
        try:
            client = await TelegramClient(None, api_id, api_hash).start(
                bot_token=bot_token
            )
            logging.info("Successfully initiate bot")
        except UnauthorizedError:
            logging.error(
                "Unauthorized access. Please check your Telethon API ID, API hash"
            )
            raise UnauthorizedError
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            raise e

        client.add_event_handler(security_check)

        # Search feature
        client.add_event_handler(search_handler)
        logging.debug("Search handler added")

        # Terminal bash feature
        client.add_event_handler(bash_handler)
        logging.debug("Bash handler added")

        # Clear chat history feature
        client.add_event_handler(clear_handler)
        logging.debug("Clear handler added")

        # Switch gpt model
        client.add_event_handler(switch_model_handler)
        logging.debug("Switch model handler added")

        # User and group chat
        client.add_event_handler(bard_chat_handler)
        logging.debug("Bard chat handler added")
        client.add_event_handler(bing_chat_handler)
        logging.debug("Bing chat handler added")
        client.add_event_handler(gemini_chat_handler)
        logging.debug("Gemini chat handler added")
        client.add_event_handler(senpai_chat_handler)
        logging.debug("Senpai chat handler added")
        client.add_event_handler(group_chat_handler)
        logging.debug("Group chat handler added")
        client.add_event_handler(user_chat_handler)
        logging.debug("User chat handler added")

        print("Bot is running")
        await client.run_until_disconnected()
