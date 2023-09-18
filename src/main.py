import signal
from bot import Bot
import json
import os
import sys
import asyncio
from pathlib import Path
from log import getlogger

logger = getlogger()


async def main():
    config_path = Path(os.path.dirname(__file__)).parent / "config.json"
    if os.path.isfile(config_path):
        fp = open("config.json", "r", encoding="utf-8")
        try:
            config = json.load(fp)
        except Exception as e:
            logger.error(e, exc_info=True)
            sys.exit(1)

        mattermost_bot = Bot(
            server_url=config.get("server_url"),
            email=config.get("email"),
            password=config.get("password"),
            username=config.get("username"),
            port=config.get("port"),
            scheme=config.get("scheme"),
            openai_api_key=config.get("openai_api_key"),
            gpt_api_endpoint=config.get("gpt_api_endpoint"),
            gpt_model=config.get("gpt_model"),
            max_tokens=config.get("max_tokens"),
            top_p=config.get("top_p"),
            presence_penalty=config.get("presence_penalty"),
            frequency_penalty=config.get("frequency_penalty"),
            reply_count=config.get("reply_count"),
            system_prompt=config.get("system_prompt"),
            temperature=config.get("temperature"),
            image_generation_endpoint=config.get("image_generation_endpoint"),
            image_generation_backend=config.get("image_generation_backend"),
            timeout=config.get("timeout"),
        )

    else:
        mattermost_bot = Bot(
            server_url=os.environ.get("SERVER_URL"),
            email=os.environ.get("EMAIL"),
            password=os.environ.get("PASSWORD"),
            username=os.environ.get("USERNAME"),
            port=os.environ.get("PORT"),
            scheme=os.environ.get("SCHEME"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            gpt_api_endpoint=os.environ.get("GPT_API_ENDPOINT"),
            gpt_model=os.environ.get("GPT_MODEL"),
            max_tokens=os.environ.get("MAX_TOKENS"),
            top_p=os.environ.get("TOP_P"),
            presence_penalty=os.environ.get("PRESENCE_PENALTY"),
            frequency_penalty=os.environ.get("FREQUENCY_PENALTY"),
            reply_count=os.environ.get("REPLY_COUNT"),
            system_prompt=os.environ.get("SYSTEM_PROMPT"),
            temperature=os.environ.get("TEMPERATURE"),
            image_generation_endpoint=os.environ.get("IMAGE_GENERATION_ENDPOINT"),
            image_generation_backend=os.environ.get("IMAGE_GENERATION_BACKEND"),
            timeout=os.environ.get("TIMEOUT"),
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
