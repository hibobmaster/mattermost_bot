import signal
from bot import Bot
import json
import os
import asyncio
from pathlib import Path
from log import getlogger

logger = getlogger()


async def main():
    config_path = Path(os.path.dirname(__file__)).parent / "config.json"
    if os.path.isfile(config_path):
        fp = open("config.json", "r", encoding="utf-8")
        config = json.load(fp)

        mattermost_bot = Bot(
            server_url=config.get("server_url"),
            access_token=config.get("access_token"),
            login_id=config.get("login_id"),
            password=config.get("password"),
            username=config.get("username"),
            openai_api_key=config.get("openai_api_key"),
            bing_auth_cookie=config.get("bing_auth_cookie"),
            pandora_api_endpoint=config.get("pandora_api_endpoint"),
            pandora_api_model=config.get("pandora_api_model"),
            port=config.get("port"),
            scheme=config.get("scheme"),
            timeout=config.get("timeout"),
            gpt_engine=config.get("gpt_engine"),
        )

    else:
        mattermost_bot = Bot(
            server_url=os.environ.get("SERVER_URL"),
            access_token=os.environ.get("ACCESS_TOKEN"),
            login_id=os.environ.get("LOGIN_ID"),
            password=os.environ.get("PASSWORD"),
            username=os.environ.get("USERNAME"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            bing_auth_cookie=os.environ.get("BING_AUTH_COOKIE"),
            pandora_api_endpoint=os.environ.get("PANDORA_API_ENDPOINT"),
            pandora_api_model=os.environ.get("PANDORA_API_MODEL"),
            port=os.environ.get("PORT"),
            scheme=os.environ.get("SCHEME"),
            timeout=os.environ.get("TIMEOUT"),
            gpt_engine=os.environ.get("GPT_ENGINE"),
        )

    await mattermost_bot.login()

    task = asyncio.create_task(mattermost_bot.run())

    # handle signal interrupt
    loop = asyncio.get_running_loop()
    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.create_task(mattermost_bot.close(task)),
        )

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
