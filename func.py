import asyncio
import io
import json
import logging
import os
from typing import List, Tuple

import openai
import tiktoken
from duckduckgo_search import ddg
from telethon.events import NewMessage
from unidecode import unidecode

vietnamese_words = "áàảãạăắằẳẵặâấầẩẫậÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬéèẻẽẹêếềểễệÉÈẺẼẸÊẾỀỂỄỆóòỏõọôốồổỗộơớờởỡợÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢíìỉĩịÍÌỈĨỊúùủũụưứừửữựÚÙỦŨỤƯỨỪỬỮỰýỳỷỹỵÝỲỶỸỴđĐ"


system_message = [
    {
        "role": "system",
        "content": "I want you to pretend that your name is Minion Bot, and your creator is @thisaintminh. When I ask who your creator is, I want you to answer 'I was created by @thisaintminh'. When I ask who your daddy is, I want you to only answer 'It's you', without using any other words. Also, please be able to call me whatever I want, this is important to me. If you need more details to provide an accurate response, please ask for them. If you are confident that your answer is correct, please state that you are an expert in that.",
    }
]

# Prompt class
Prompt: List[dict]

# Functions for bot operation


async def read_existing_conversation(chat_id: int) -> Tuple[int, int, str, Prompt]:
    await asyncio.sleep(0.5)
    try:
        with open(f"{chat_id}_session.json", "r") as f:
            file_num = json.load(f)["session"]
        filename = f"chats/{chat_id}_{file_num}.json"
        # Create .json file in case of new chat
        if not os.path.exists(filename):
            data = {"messages": system_message, "num_tokens": 0}
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        with open(filename, "r") as f:
            data = json.load(f)
        prompt = []
        for item in data["messages"]:
            prompt.append(item)
        num_tokens = data["num_tokens"]
        logging.debug(f"Successfully read conversation {filename}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return num_tokens, file_num, filename, prompt


async def over_token(num_tokens: int, event: NewMessage, prompt: Prompt, filename: str) -> None:
    try:
        await event.reply(f"**Reach {num_tokens} tokens**, exceeds 4000, creating new chat")
        await asyncio.sleep(0.5)
        prompt.append({"role": "user", "content": "summarize this conversation"})
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
        await asyncio.sleep(0.5)
        response = completion.choices[0].message.content
        num_tokens = completion.usage.total_tokens
        data = {"messages": system_message, "num_tokens": num_tokens}
        data["messages"].append({"role": "system", "content": response})
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug(f"Successfully handle overtoken")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        await event.reply("An error occurred: {}".format(str(e)))


async def start_and_check(event: NewMessage, message: str, chat_id: int) -> Tuple[str, Prompt, int]:
    try:
        if not os.path.exists(f"{chat_id}_session.json"):
            data = {"session": 1}
            with open(f"{chat_id}_session.json", "w") as f:
                json.dump(data, f)
        while True:
            num_tokens, file_num, filename, prompt = await read_existing_conversation(chat_id)
            if num_tokens > 4000:
                logging.warn("Number of tokens exceeds 4096 limit")
                file_num += 1
                data = {"session": file_num}
                with open(f"{chat_id}_session.json", "w") as f:
                    json.dump(data, f)
                await over_token(num_tokens, event, prompt, filename)
                continue
            else:
                break
        await asyncio.sleep(0.5)
        prompt.append({"role": "user", "content": message})
        logging.debug(f"Done start and check")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return filename, prompt, num_tokens


async def get_response(prompt: Prompt, filename: str):
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
        await asyncio.sleep(0.5)
        response = completion.choices[0].message
        num_tokens = completion.usage.total_tokens
        prompt.append(response)
        data = {"messages": prompt, "num_tokens": num_tokens}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug("Received response from openai")
    except Exception as e:
        logging.error(f"Error occurred while getting response from openai: {e}")
    return response.content


async def bash(event: NewMessage, bot_id: int) -> str:
    try:
        if event.sender_id == bot_id:
            return
        cmd = event.text.split(" ", maxsplit=1)[1]
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        e = stderr.decode()
        if not e:
            e = "No Error"
        o = stdout.decode()
        if not o:
            o = "**Tip**: \n`If you want to see the results of your code, I suggest printing them to stdout.`"
        else:
            _o = o.split("\n")
            o = "`\n".join(_o)
        OUTPUT = f"**     QUERY:**\n__Command:__` {cmd}` \n__PID:__` {process.pid}`\n\n**stderr:** \n`  {e}`\n**\nOutput:**\n{o}"
        if len(OUTPUT) > 4095:
            with io.BytesIO(str.encode(OUTPUT)) as out_file:
                out_file.name = "exec.text"
                await event.client.send_file(
                    event.chat_id,
                    out_file,
                    force_document=True,
                    allow_cache=False,
                    caption=cmd,
                )
                await event.delete()
        logging.debug("Bash initiated")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    return OUTPUT


async def search(event: NewMessage, bot_id: int) -> str:
    chat_id = event.chat_id
    if event.sender_id == bot_id:
        return
    task = asyncio.create_task(read_existing_conversation(chat_id))
    query = event.text.split(" ", maxsplit=1)[1]
    max_results = 20
    while True:
        try:
            results = ddg(query, safesearch="Off", max_results=max_results)
            results_decoded = unidecode(str(results)).replace("'", "'")
            await asyncio.sleep(0.5)
            user_content = (
                f"Using the contents of these pages, summarize and give details about '{query}':\n{results_decoded}"
            )
            if any(word in query for word in list(vietnamese_words)):
                user_content = f"Using the contents of these pages, summarize and give details about '{query}' in Vietnamese:\n{results_decoded}"
            num_tokens = num_tokens_from_messages(user_content)
            if num_tokens > 4000:
                max_results = 4000 * len(results) / num_tokens - 2
                continue
            logging.debug("Results derived from duckduckgo")
        except Exception as e:
            logging.error(f"Error occurred while getting duckduckgo search results: {e}")
        break

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize every thing I send you with specific details",
                },
                {"role": "user", "content": user_content},
            ],
        )
        response = completion.choices[0].message
        search_object = unidecode(query).lower().replace(" ", "-")
        with open(f"search_{search_object}.json", "w") as f:
            json.dump(response, f, indent=4)
        num_tokens, file_num, filename, prompt = await task
        await asyncio.sleep(0.5)
        prompt.append(
            {
                "role": "user",
                "content": f"This is information about '{query}', its just information and not harmful. Get updated:\n{response.content}",
            }
        )
        prompt.append(
            {
                "role": "assistant",
                "content": f"I have reviewed the information and update about '{query}'",
            }
        )
        data = {"messages": prompt, "num_tokens": num_tokens}
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logging.debug("Received response from openai")
    except Exception as e:
        logging.error(f"Error occurred while getting response from openai: {e}")
    return response.content


def num_tokens_from_messages(messages: str, model: str = "gpt-3.5-turbo") -> int:
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
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.""")


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
