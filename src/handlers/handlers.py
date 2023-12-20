import asyncio
import glob
import logging
import random

from telethon.events import NewMessage, StopPropagation, register
from telethon.tl.custom import Button
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction

import src.utils.utils
from src.functions.additional_func import bash, search
from src.functions.chat_func import (
    get_bard_response,
    get_bing_response,
    get_gemini_response,
    get_gemini_vison_response,
    get_openai_response,
    process_and_send_mess,
    start_and_check,
)
from src.utils import (
    ALLOW_USERS,
    LOG_PATH,
    MODEL_DICT,
    RANDOM_ACTION,
    SYS_MESS_FRIENDLY,
    SYS_MESS_SENPAI,
    check_chat_type,
)


@register(NewMessage())
async def security_check(event: NewMessage) -> None:
    chat_id = event.chat_id
    if chat_id not in ALLOW_USERS:
        client = event.client
        await client.send_message(
            chat_id, f"This is personal property, you are not allowed to proceed!"
        )
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

    # Under maintainance
    await event.reply("**Cannot use this anymore**")
    raise StopPropagation

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


@register(NewMessage(pattern="/gemini"))
async def gemini_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type == "User":
        message = message.split(" ", maxsplit=1)[1]
    logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))

    try:
        file_name = await event.download_media("temp")
    except:
        logging.error(f"Error occurred when downloading media: {e}")
        await event.reply("**Error occurred when downloading media**")
        raise StopPropagation

    # Inialize
    loop = asyncio.get_event_loop()

    # Get response from openAI
    if not file_name:
        future = loop.run_in_executor(None, get_gemini_response, message)
    else:
        future = loop.run_in_executor(
            None, get_gemini_vison_response, message, file_name
        )
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


@register(NewMessage(pattern="/switchmodel"))
async def switch_model_handler(event: NewMessage) -> None:
    model = event.raw_text.split(" ", maxsplit=1)[1]
    client = event.client
    try:
        if model not in MODEL_DICT:
            available_models = "**, **".join(MODEL_DICT.keys())
            await client.send_message(
                event.chat_id,
                f"Model not found, available models: **{available_models}**",
            )
        elif MODEL_DICT[model][0] == src.utils.utils.model:
            await client.send_message(
                event.chat_id, f"**{MODEL_DICT[model][0]}** is being used already"
            )
        else:
            src.utils.utils.model = MODEL_DICT[model][0]  # Overwrite system MODEL
            src.utils.utils.max_token = MODEL_DICT[model][1]
            # TODO: This is wrong but save it for future switchtone
            # if len(glob.glob(f"{LOG_PATH}chats/history/{event.chat_id}*")) > 0:
            #     await client.send_message(
            #         event.chat_id,
            #         f"Successfully set model to **{MODEL_DICT[model][0]}**\n\nSwitching model requires a chat history reset, please perform /clear and the change will be applied.",
            #     )
            # else:
            await client.send_message(
                event.chat_id,
                f"Successfully set model to **{MODEL_DICT[model][0]}**",
            )
            logging.debug(f"Model switched to {MODEL_DICT[model][0]}")
    except Exception as e:
        logging.error(f"Error occurred while switching model: {e}")
    raise StopPropagation


@register(NewMessage(pattern="/senpai"))
async def senpai_chat_handler(event: NewMessage) -> None:
    # Get info
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type == "User":
        message = message.split(" ", maxsplit=1)[1]
    logging.debug(f"Check chat type {chat_type} done")
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    src.utils.utils.sys_mess = SYS_MESS_SENPAI  # Overwrite system mess

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
    src.utils.utils.sys_mess = SYS_MESS_SENPAI  # Overwrite system mess

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
    src.utils.utils.sys_mess = SYS_MESS_FRIENDLY  # Overwrite system mess

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
