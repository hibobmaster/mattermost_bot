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
            image_generation_size=config.get("image_generation_size"),
            image_format=config.get("image_format"),
            timeout=config.get("timeout"),
        )

    else:
        mattermost_bot = Bot(
            server_url=os.environ.get("SERVER_URL"),
            email=os.environ.get("EMAIL"),
            password=os.environ.get("PASSWORD"),
            username=os.environ.get("USERNAME"),
            port=int(os.environ.get("PORT", 443)),
            scheme=os.environ.get("SCHEME"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            gpt_api_endpoint=os.environ.get("GPT_API_ENDPOINT"),
            gpt_model=os.environ.get("GPT_MODEL"),
            max_tokens=int(os.environ.get("MAX_TOKENS", 4000)),
            top_p=float(os.environ.get("TOP_P", 1.0)),
            presence_penalty=float(os.environ.get("PRESENCE_PENALTY", 0.0)),
            frequency_penalty=float(os.environ.get("FREQUENCY_PENALTY", 0.0)),
            reply_count=int(os.environ.get("REPLY_COUNT", 1)),
            system_prompt=os.environ.get("SYSTEM_PROMPT"),
            temperature=float(os.environ.get("TEMPERATURE", 0.8)),
            image_generation_endpoint=os.environ.get("IMAGE_GENERATION_ENDPOINT"),
            image_generation_backend=os.environ.get("IMAGE_GENERATION_BACKEND"),
            image_generation_size=os.environ.get("IMAGE_GENERATION_SIZE"),
            image_format=os.environ.get("IMAGE_FORMAT"),
            timeout=float(os.environ.get("TIMEOUT", 120.0)),
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
