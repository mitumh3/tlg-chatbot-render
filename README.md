# OpenAI-integrated Telegram Chatbot

This is a project to create a Telegram chatbot that is integrated with OpenAI to enable natural language processing and intelligent responses in messaging.

Additionally, we will provide guidelines for deploying the bot with zero downtime on Render for free, an alternative to Heroku.

The following set of comprehensive instructions will guide you through creating the chatbot, which includes registering a new Telegram bot, configuring OpenAI API keys, integrating the two services, and deploying the application as a 24/7 service.

## PREREQUISITES

To run this project, you will need the following:

- A Github account (Obviously)
- An OpenAI API Key
- Telegram App ID and hash
- A Telegram Bot token
- A Render account
- Python (version 3.8 or newer) - if running in local

## INSTALLATION

1. Clone this repository by typing this command in the terminal.

```bash
git clone https://github.com/mitumh3/tlg-chatbot-render.git
```

2. Install the required packages by this command.

```bash
pip install -r requirements.txt
```

## SETUP KEYS

### Get OpenAI API Key

1. Make sure you have an OpenAI account.
2. Go to <https://platform.openai.com/account/api-keys> to create or get an API Key.

> Note: In gpt-3.5-turbo model, $0.002 will be charged for 1k tokens. However, there are account plans that give you certain amount of granted credit (my case is a free trial of $18).

### Get Telegram App ID and Hash

To get the API ID and Hash of your Telegram app (your bot), you need to follow the below steps:

1. Please ensure that you have a Telegram account and are already logged in on your phone.
2. Open your web browser and go to <https://my.telegram.org/auth>.
3. Enter your phone number associated with your Telegram account and click on the Next button.
4. An OTP will be sent to your Telegram app, enter the OTP in the given field.
5. Now, you will be redirected to the Developer Tools page. Here, you can find the API ID and Hash after clicking "Create a new application" section and fill out the form.
6. Note down the API ID and Hash somewhere securely.

> Note: Please make sure you keep your API ID and Hash secret and do not share them with anyone else as they can be used to access your Telegram account, groups, and channels.

### Get a Telegram Bot token

1. Visit <https://telegram.me/BotFather> or find @BotFather on your Telegram to register a new bot.
2. Send `/newbot` command to BotFather.
3. Set a name for the bot and a username (ending with 'bot').
4. When registration process is completed, BotFather will provide an HTTP API token for the bot.
5. You should further configure the bot for group chat permission by: Bot Settings >> Group Privacy >> Turn Off

### Declare your keys in environment

Run the bot in local will required creating an `.env` file with the following contents:

```python
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
API_ID="YOUR_TELEGRAM_APP_ID"
API_HASH="YOUR_TELEGRAM_APP_HASH"
BOTTOKEN=YOUR_BOT_TOKEN
```

> Note:
>
> - Remember to replace YOUR_OPENAI_API_KEY, YOUR_BOT_TOKEN, YOUR_TELEGRAM_APP_ID, and YOUR_TELEGRAM_APP_HASH with the real keys that you've just got from the above.
> - All the keys should be put in quotes as a string, except YOUR_BOT_TOKEN since it is an integer.
> - For security, `.env` file is only suitable for local run. In case of deployment, your keys should be kept as `SECRETS` or `ENVIRONMENT VARIABLES` that can only be accessed by you.

## RUN BOT

Run the command below in your terminal to initiate the bot.

```bash
uvicorn src.main:app --port=${PORT:-8080}
```

## FEATURES

v1.0.x will include the following use:

- Private chat: You can freely chat with the bot using the bot username (@your_bot_username) derived from the BotFather
- Group chat: The bot can be invited into groupchat and user can interact with it through command `/slave`.
- Bash: `/bash {command}` to run bash script.
- Clear: `/clear` to clear all existing conversations.
- Search: `/search {keywords}` to send search request to duckduckgo and openAI will summarize the search for you. Tip: you can update bot's knowledge with this, since search summary will be added to your current conversation.

Example:

- In private: "Who is your creator?"
- Group chat: "/slave Who's your daddy?"
- "/bash ls -a"
- "/clear"
- "/search avatar 2023"

---

# Deploy bot on Render

The bot can be deployed freely on <https://render.com> for 24/7 runtime as a web application.

## SETUP RENDER

1. Make sure you have a Github repo containing all the files.
2. Get yourself a render.com account (Logging in with your github account should be the most convenience).
3. Follow these clicks: Dashboard >> New >> Web Service
4. Choose your Github repo.
5. Complete the form with:

- Name, Region
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn src.main:app --port=${PORT:-8080} --log-config=log/logging.ini`
- Instance Type: Free
- Click on Advanced and add the 4 keys as environment variables. Add another variable: `PYTHON_VERSION` with value of `3.10.2` to define the runtime version.
- Health Check Path: `/health`
- Auto-Deploy: No

## RUN

1. For the first time, click Create Web Service after filling out the form to start deploying the bot.
2. Manual deployment can be performed in your bot web service found in Dashboard of render.

> Note:
>
> - The 4 keys (`OPENAI_API_KEY`, `BOTTOKEN`, `API_ID`, `API_HASH`) and their values don't need quotes.
> - Logs can be found on <https://{your_setup_name}.onrender.com/log> and additional bash command can be executed on <https://{your_setup_name}.onrender.com/terminal>
> - Deployment will take about 15 minutes to complete, but some problems within the server can happen if we interact with the bots in this period (Usually, the bot will get duplicated responses. In case of private chats, without preceded command in message, the bot will "chat" to itself and create a messy looped conversation that will burn out your credits). Therefore, a total of 30m to 1 hour should be taken to avoid the above problem. Or you can chat in a group with preceded commands.

---

## Possible Improvements

- Add more functionalities to the bot.
- Increase the accuracy of OpenAI responses.
- Refine the conversation handling.
- Fix problem that Render server will be reset after every 15 minutes.
- Fix bot looped conversation in private chat at deployment start up.
- To limit the number of tokens generated for each prompt, the tiktoken package is commonly used. However, this package can only be used on newer versions of Python, which can be inconvenient. As a solution, we recommend removing the use of tiktoken and exploring alternatives for limiting token usage.

## Contributing

We are grateful for contributions of any magnitude. Also, a big thanks to DirtyG2120 for his exceptional and expert contribution.
