from telethon import events
import json
import asyncio
import os
import openai
import io


# Function for bot operation
def start_and_check(system_message, message, chat_id):
    if not os.path.exists(f"{chat_id}_session.json"):
        data = {"session": 1}
        with open(f"{chat_id}_session.json", 'w') as f:
            json.dump(data, f)
    while True:
        with open(f"{chat_id}_session.json", 'r') as f:
            file_num=json.load(f)['session']
        filename = f'chats/{chat_id}_{file_num}.json'
            # Create .json file in case of new chat
        if not os.path.exists(filename):
            data = {
                    "messages": [{
                                "role": "system",
                                "content": system_message
                                }],
                    "num_tokens": 0
                    }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        with open(filename, 'r') as f:
            data = json.load(f)
        prompt = []
        for item in data['messages']:
            prompt.append(item)
            
        num_tokens=data["num_tokens"]
        if num_tokens > 4000:
            file_num += 1
            data = {"session": file_num}
            with open(f"{chat_id}_session.json", 'w') as f:
                json.dump(data, f)
            events.reply(f"{num_tokens} exceeds 4096, creating new chat")
            prompt.append({
                "role": "user",
                "content": "summarize this conversation"
            })
            completion = openai.ChatCompletion.create(
                                                        model='gpt-3.5-turbo',
                                                        messages=prompt
                                                    )
            response = completion.choices[0].message.content
            num_tokens = completion.usage.total_tokens
            data = {
                "messages": [{
                            "role": "system",
                            "content": system_message
                            },
                            {
                            "role": "system",
                            "content": response
                            }],
                "num_tokens": num_tokens
                    }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            continue
        else: break

    prompt.append({
                    "role": "user",
                    "content": message
                }) 
    return filename, prompt, num_tokens

def get_response(prompt, filename):
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=prompt
    )
    response = completion.choices[0].message.content
    num_tokens = completion.usage.total_tokens
    prompt.append(
        {
            "role": "assistant",
            "content": response
        })
    data= {"messages":prompt, "num_tokens":num_tokens}
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    return response

async def bash(event, bot_id):
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
    OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"
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
    await event.reply(OUTPUT)
