import logging

from telethon.events import NewMessage, StopPropagation, register
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction

from src.functions.additional_func import bash, search
from src.functions.chat_func import get_response, start_and_check
from src.utils import check_chat_type


@register(NewMessage(pattern="/search"))
async def search_handler(event: NewMessage) -> None:
    client = event.client
    chat_id = event.chat_id
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    response = await search(event)
    try:
        await client.send_message(chat_id, f"__Here is your search:__\n{response}")
        logging.info(f"Sent /search to {chat_id}")
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
        logging.info(f"Sent /bash to {event.chat_id}")
    except Exception as e:
        logging.error(f"Error occurred while responding /bash cmd: {e}")
    raise StopPropagation


@register(NewMessage(pattern="/clear"))
async def clear_handler(event: NewMessage) -> None:
    client = event.client
    event.text = "/bash rm log/chats/*"
    response = await bash(event)
    try:
        await client.send_message(event.chat_id, f"{response}")
        logging.info(f"Sent /bash to {event.chat_id}")
    except Exception as e:
        logging.error(f"Error occurred while responding /bash cmd: {e}")
    raise StopPropagation


@register(NewMessage)
async def user_chat_handler(event: NewMessage) -> None:
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "User":
        return
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    filename, prompt = await start_and_check(event, message, chat_id)
    # Get response from openai and send to chat_id
    responses = await get_response(prompt, filename)
    try:
        for response in responses:
            await client.send_message(chat_id, response)
        logging.info(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")


@register(NewMessage(pattern="/slave"))
async def group_chat_handler(event: NewMessage) -> None:
    chat_type, client, chat_id, message = await check_chat_type(event)
    if chat_type != "Group":
        return
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    filename, prompt = await start_and_check(event, message, chat_id)
    # Get response from openai and send to chat_id
    responses = await get_response(prompt, filename)
    try:
        for response in responses:
            await client.send_message(chat_id, response)
        logging.info(f"Sent message to {chat_id}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        await event.reply("**Fail to get response**")
    await client.action(chat_id, "cancel")
