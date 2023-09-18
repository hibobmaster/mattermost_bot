from mattermostdriver import AsyncDriver
from typing import Optional
import json
import asyncio
import re
import os
from gptbot import Chatbot
from log import getlogger
import httpx

logger = getlogger()


class Bot:
    def __init__(
        self,
        server_url: str,
        username: str,
        email: str,
        password: str,
        port: Optional[int] = 443,
        scheme: Optional[str] = "https",
        openai_api_key: Optional[str] = None,
        gpt_api_endpoint: Optional[str] = None,
        gpt_model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        reply_count: Optional[int] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        image_generation_endpoint: Optional[str] = None,
        image_generation_backend: Optional[str] = None,
        timeout: Optional[float] = 120.0,
    ) -> None:
        if server_url is None:
            raise ValueError("server url must be provided")

        if port is None:
            self.port = 443
        else:
            port = int(port)
            if port <= 0 or port > 65535:
                raise ValueError("port must be between 0 and 65535")
            self.port = port

        if scheme is None:
            self.scheme = "https"
        else:
            if scheme.strip().lower() not in ["http", "https"]:
                raise ValueError("scheme must be either http or https")
            self.scheme = scheme

        # @chatgpt
        if username is None:
            raise ValueError("username must be provided")
        else:
            self.username = username

        self.openai_api_key: str = openai_api_key
        self.gpt_api_endpoint = (
            gpt_api_endpoint or "https://api.openai.com/v1/chat/completions"
        )
        self.gpt_model: str = gpt_model or "gpt-3.5-turbo"
        self.max_tokens: int = max_tokens or 4000
        self.top_p: float = top_p or 1.0
        self.temperature: float = temperature or 0.8
        self.presence_penalty: float = presence_penalty or 0.0
        self.frequency_penalty: float = frequency_penalty or 0.0
        self.reply_count: int = reply_count or 1
        self.system_prompt: str = (
            system_prompt
            or "You are ChatGPT, \
            a large language model trained by OpenAI. Respond conversationally"
        )
        self.image_generation_endpoint: str = image_generation_endpoint
        self.image_generation_backend: str = image_generation_backend
        self.timeout = timeout or 120.0

        #  httpx session
        self.httpx_client = httpx.AsyncClient()

        # initialize Chatbot object
        self.chatbot = Chatbot(
            aclient=self.httpx_client,
            api_key=self.openai_api_key,
            api_url=self.gpt_api_endpoint,
            engine=self.gpt_model,
            timeout=self.timeout,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            reply_count=self.reply_count,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
        )

        # login relative info
        if email is None and password is None:
            raise ValueError("user email and password must be provided")

        self.driver = AsyncDriver(
            {
                "login_id": email,
                "password": password,
                "url": server_url,
                "port": self.port,
                "request_timeout": self.timeout,
                "scheme": self.scheme,
            }
        )

        # regular expression to match keyword
        self.gpt_prog = re.compile(r"^\s*!gpt\s*(.+)$")
        self.chat_prog = re.compile(r"^\s*!chat\s*(.+)$")
        self.pic_prog = re.compile(r"^\s*!pic\s*(.+)$")
        self.help_prog = re.compile(r"^\s*!help\s*.*$")
        self.new_prog = re.compile(r"^\s*!new\s*.*$")

    # close session
    async def close(self, task: asyncio.Task) -> None:
        await self.httpx_client.aclose()
        self.driver.disconnect()
        task.cancel()

    async def login(self) -> None:
        await self.driver.login()

    async def run(self) -> None:
        await self.driver.init_websocket(self.websocket_handler)

    # websocket handler
    async def websocket_handler(self, message) -> None:
        logger.info(message)
        response = json.loads(message)
        if "event" in response:
            event_type = response["event"]
            if event_type == "posted":
                raw_data = response["data"]["post"]
                raw_data_dict = json.loads(raw_data)
                user_id = raw_data_dict["user_id"]
                root_id = (
                    raw_data_dict["root_id"]
                    if raw_data_dict["root_id"]
                    else raw_data_dict["id"]
                )
                channel_id = raw_data_dict["channel_id"]
                sender_name = response["data"]["sender_name"]
                raw_message = raw_data_dict["message"]

                try:
                    asyncio.create_task(
                        self.message_callback(
                            raw_message, channel_id, user_id, sender_name, root_id
                        )
                    )
                except Exception as e:
                    await self.send_message(channel_id, f"{e}", root_id)

    # message callback
    async def message_callback(
        self,
        raw_message: str,
        channel_id: str,
        user_id: str,
        sender_name: str,
        root_id: str,
    ) -> None:
        # prevent command trigger loop
        if sender_name != self.username:
            message = raw_message

            if (
                self.openai_api_key is not None
                or self.gpt_api_endpoint != "https://api.openai.com/v1/chat/completions"
            ):
                # !gpt command trigger handler
                if self.gpt_prog.match(message):
                    prompt = self.gpt_prog.match(message).group(1)
                    try:
                        response = await self.chatbot.oneTimeAsk(prompt)
                        await self.send_message(channel_id, f"{response}", root_id)
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

                # !chat command trigger handler
                elif self.chat_prog.match(message):
                    prompt = self.chat_prog.match(message).group(1)
                    try:
                        response = await self.chatbot.ask_async(
                            prompt=prompt, convo_id=user_id
                        )
                        await self.send_message(channel_id, f"{response}", root_id)
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

            # !new command trigger handler
            if self.new_prog.match(message):
                self.chatbot.reset(convo_id=user_id)
                try:
                    await self.send_message(
                        channel_id,
                        "New conversation created, "
                        + "please use !chat to start chatting!",
                        root_id,
                    )
                except Exception as e:
                    logger.error(e, exc_info=True)
                    raise Exception(e)

            # !pic command trigger handler
            if self.pic_prog.match(message):
                prompt = self.pic_prog.match(message).group(1)
                # generate image
                try:
                    links = await self.imagegen.get_images(prompt)
                    image_path = await self.imagegen.save_images(links, "images")
                except Exception as e:
                    logger.error(e, exc_info=True)
                    raise Exception(e)

                # send image
                try:
                    await self.send_file(channel_id, prompt, image_path)
                except Exception as e:
                    logger.error(e, exc_info=True)
                    raise Exception(e)

            # !help command trigger handler
            if self.help_prog.match(message):
                try:
                    await self.send_message(channel_id, self.help(), root_id)
                except Exception as e:
                    logger.error(e, exc_info=True)

    # send message to room
    async def send_message(self, channel_id: str, message: str, root_id: str) -> None:
        await self.driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "message": message,
                "root_id": root_id,
            }
        )

    # send file to room
    async def send_file(self, channel_id: str, message: str, filepath: str) -> None:
        filename = os.path.split(filepath)[-1]
        try:
            file_id = await self.driver.files.upload_file(
                channel_id=channel_id,
                files={
                    "files": (filename, open(filepath, "rb")),
                },
            )["file_infos"][0]["id"]
        except Exception as e:
            logger.error(e, exc_info=True)
            raise Exception(e)

        try:
            await self.driver.posts.create_post(
                options={
                    "channel_id": channel_id,
                    "message": message,
                    "file_ids": [file_id],
                }
            )
            # remove image after posting
            os.remove(filepath)
        except Exception as e:
            logger.error(e, exc_info=True)
            raise Exception(e)

    # !help command function
    def help(self) -> str:
        help_info = (
            "!gpt [content], generate response without context conversation\n"
            + "!chat [content], chat with context conversation\n"
            + "!pic [prompt], Image generation with DALL·E or LocalAI or stable-diffusion-webui\n"  # noqa: E501
            + "!new, start a new conversation\n"
            + "!help, help message"
        )
        return help_info