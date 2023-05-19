import asyncio
import logging
import random

import src.utils.utils
from src.functions.additional_func import bash, search
from src.functions.chat_func import (
    get_bard_response,
    get_bing_response,
    get_openai_response,
    process_and_send_mess,
    start_and_check,
)
from src.utils import LOG_PATH, RANDOM_ACTION, SYS_MESS_SENPAI, check_chat_type
from telethon.events import NewMessage, StopPropagation, register
from telethon.tl.custom import Button
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction


@register(NewMessage(pattern="/cancel"))
async def cancel_handler(event: NewMessage) -> None:
    raise StopPropagation


@register(NewMessage(pattern="/search"))
async def search_handler(event: NewMessage) -> None:
    client = event.client
    chat_id = event.chat_id
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    response = await search(event)
    try:
        await client.send_message(chat_id, f"__Here is your search:__\n{response}")
        logging.debug(f"Sent /search to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation


@register(NewMessage(pattern="/bash"))
async def bash_handler(event: NewMessage) -> None:
    client = event.client
    response = await bash(event)
    try:
        await client.send_message(event.chat_id, f"{response}")
        logging.debug(f"Sent /bash to {event.chat_id}")
    except Exception as e:
        logging.error(f"Error occurred while responding /bash cmd: {e}")
    raise StopPropagation


@register(NewMessage(pattern="/clear"))
async def clear_handler(event: NewMessage) -> None:
    client = event.client
    event.text = f"/bash rm {LOG_PATH}chats/history/{event.chat_id}*"
    response = await bash(event)
    try:
        await client.send_message(event.chat_id, f"{response}")
        logging.debug(f"Sent /bash to {event.chat_id}")
    except Exception as e:
        logging.error(f"Error occurred while responding /bash cmd: {e}")
    raise StopPropagation


@register(NewMessage(pattern="/bard"))
async def bard_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type == "User":
        message = message.split(" ", maxsplit=1)[1]
    logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))

    # Inialize
    loop = asyncio.get_event_loop()

    # Get response from openAI
    future = loop.run_in_executor(None, get_bard_response, message)
    while not future.done():  # Loop of random actions indicates running process
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response = await future

    # Send response to chat id
    try:
        await process_and_send_mess(event, response)
        logging.debug(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling {chat_type} chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation


@register(NewMessage(pattern="/bing"))
async def bing_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type == "User":
        message = message.split(" ", maxsplit=1)[1]
    logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))

    # Inialize
    loop = asyncio.get_event_loop()

    # Get response from openAI
    future = loop.run_in_executor(None, get_bing_response, message)
    while not future.done():  # Loop of random actions indicates running process
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response, suggest_lst = await future

    buttons = [
        [Button.text(text=f"/bing {text}", single_use=True)] for text in suggest_lst
    ]
    buttons.append([Button.text(text=f"/cancel", single_use=True)])
    # Send response to chat id
    try:
        await event.client.send_message(
            event.chat_id,
            response,
            background=True,
            silent=True,
            buttons=buttons,
        )
        logging.debug(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling {chat_type} chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation


@register(NewMessage(pattern="/senpai"))
async def senpai_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type == "User":
        message = message.split(" ", maxsplit=1)[1]
    logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    src.utils.utils.SYS_MESS = SYS_MESS_SENPAI  # Overwrite system mess

    # Inialize
    filename, prompt = await start_and_check(event, message, chat_id)
    loop = asyncio.get_event_loop()

    # Get response from openAI
    future = loop.run_in_executor(None, get_openai_response, prompt, filename)
    while not future.done():  # Loop of random actions indicates running process
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response = await future

    # Send response to chat id
    try:
        await process_and_send_mess(event, response)
        logging.debug(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling {chat_type} chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation


@register(NewMessage)
async def user_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "User":  # Prevent no command group chat
        return
    else:
        logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))

    # Inialize
    filename, prompt = await start_and_check(event, message, chat_id)
    loop = asyncio.get_event_loop()

    # Get response from openAI
    future = loop.run_in_executor(None, get_openai_response, prompt, filename)
    while not future.done():  # Loop of random actions indicates running process
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response = await future

    # Send response to chat id
    try:
        await process_and_send_mess(event, response)
        logging.debug(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling {chat_type} chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation


@register(NewMessage(pattern="/slave"))
async def group_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "Group":
        return
    else:
        logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))

    # Inialize
    filename, prompt = await start_and_check(event, message, chat_id)
    loop = asyncio.get_event_loop()

    # Get response from openAI
    future = loop.run_in_executor(None, get_openai_response, prompt, filename)
    while not future.done():  # Loop of random actions indicates running process
        random_choice = random.choice(RANDOM_ACTION)
        await asyncio.sleep(2)
        await client(SetTypingRequest(peer=chat_id, action=random_choice))
    response = await future

    # Send response to chat id
    try:
        await process_and_send_mess(event, response)
        logging.debug(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred when handling {chat_type} chat: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
    raise StopPropagation
