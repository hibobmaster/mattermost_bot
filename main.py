from bot import Bot
import json
import os
import asyncio


async def main():
    if os.path.exists("config.json"):
        fp = open("config.json", "r", encoding="utf-8")
        config = json.load(fp)

        mattermost_bot = Bot(
            server_url=config.get("server_url"),
            access_token=config.get("access_token"),
            login_id=config.get("login_id"),
            password=config.get("password"),
            username=config.get("username"),
            openai_api_key=config.get("openai_api_key"),
            openai_api_endpoint=config.get("openai_api_endpoint"),
            bing_api_endpoint=config.get("bing_api_endpoint"),
            bard_token=config.get("bard_token"),
            bing_auth_cookie=config.get("bing_auth_cookie"),
            port=config.get("port"),
            timeout=config.get("timeout"),
        )

    else:
        mattermost_bot = Bot(
            server_url=os.environ.get("SERVER_URL"),
            access_token=os.environ.get("ACCESS_TOKEN"),
            login_id=os.environ.get("LOGIN_ID"),
            password=os.environ.get("PASSWORD"),
            username=os.environ.get("USERNAME"),
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_api_endpoint=os.environ.get("OPENAI_API_ENDPOINT"),
            bing_api_endpoint=os.environ.get("BING_API_ENDPOINT"),
            bard_token=os.environ.get("BARD_TOKEN"),
            bing_auth_cookie=os.environ.get("BING_AUTH_COOKIE"),
            port=os.environ.get("PORT"),
            timeout=os.environ.get("TIMEOUT"),
        )

    mattermost_bot.login()

    await mattermost_bot.run()


if __name__ == "__main__":
    asyncio.run(main())
