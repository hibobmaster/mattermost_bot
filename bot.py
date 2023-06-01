from mattermostdriver import Driver
from typing import Optional
import json
import asyncio
import re
import os
import aiohttp
from askgpt import askGPT
from v3 import Chatbot
from bing import BingBot
from bard import Bardbot
from BingImageGen import ImageGenAsync
from log import getlogger
from pandora import Pandora
import uuid

logger = getlogger()


class Bot:
    def __init__(
        self,
        server_url: str,
        username: str,
        access_token: Optional[str] = None,
        login_id: Optional[str] = None,
        password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_api_endpoint: Optional[str] = None,
        bing_api_endpoint: Optional[str] = None,
        pandora_api_endpoint: Optional[str] = None,
        pandora_api_model: Optional[str] = None,
        bard_token: Optional[str] = None,
        bing_auth_cookie: Optional[str] = None,
        port: int = 443,
        timeout: int = 30,
    ) -> None:
        if server_url is None:
            raise ValueError("server url must be provided")

        if port is None:
            self.port = 443

        if timeout is None:
            self.timeout = 30

        # login relative info
        if access_token is None and password is None:
            raise ValueError("Either token or password must be provided")

        if access_token is not None:
            self.driver = Driver(
                {
                    "token": access_token,
                    "url": server_url,
                    "port": self.port,
                    "request_timeout": self.timeout,
                }
            )
        else:
            self.driver = Driver(
                {
                    "login_id": login_id,
                    "password": password,
                    "url": server_url,
                    "port": self.port,
                    "request_timeout": self.timeout,
                }
            )

        # @chatgpt
        if username is None:
            raise ValueError("username must be provided")
        else:
            self.username = username

        # openai_api_endpoint
        if openai_api_endpoint is None:
            self.openai_api_endpoint = "https://api.openai.com/v1/chat/completions"
        else:
            self.openai_api_endpoint = openai_api_endpoint

        # aiohttp session
        self.session = aiohttp.ClientSession()

        self.openai_api_key = openai_api_key
        # initialize chatGPT class
        if self.openai_api_key is not None:
            # request header for !gpt command
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            }

            self.askgpt = askGPT(
                self.session,
                self.openai_api_endpoint,
                self.headers,
            )

            self.chatbot = Chatbot(api_key=self.openai_api_key)
        else:
            logger.warning(
                "openai_api_key is not provided, !gpt and !chat command will not work"
            )

        self.bing_api_endpoint = bing_api_endpoint
        # initialize bingbot
        if self.bing_api_endpoint is not None:
            self.bingbot = BingBot(
                session=self.session,
                bing_api_endpoint=self.bing_api_endpoint,
            )
        else:
            logger.warning(
                "bing_api_endpoint is not provided, !bing command will not work"
            )

        self.pandora_api_endpoint = pandora_api_endpoint
        # initialize pandora
        if pandora_api_endpoint is not None:
            self.pandora = Pandora(
                api_endpoint=pandora_api_endpoint,
                clientSession=self.session
            )
            if pandora_api_model is None:
                self.pandora_api_model = "text-davinci-002-render-sha-mobile"
            else:
                self.pandora_api_model = pandora_api_model
        self.pandora_data = {}
        
        self.bard_token = bard_token
        # initialize bard
        if self.bard_token is not None:
            self.bardbot = Bardbot(session_id=self.bard_token)
        else:
            logger.warning("bard_token is not provided, !bard command will not work")

        self.bing_auth_cookie = bing_auth_cookie
        # initialize image generator
        if self.bing_auth_cookie is not None:
            self.imagegen = ImageGenAsync(auth_cookie=self.bing_auth_cookie)
        else:
            logger.warning(
                "bing_auth_cookie is not provided, !pic command will not work"
            )

        # regular expression to match keyword 
        self.gpt_prog = re.compile(r"^\s*!gpt\s*(.+)$")
        self.chat_prog = re.compile(r"^\s*!chat\s*(.+)$")
        self.bing_prog = re.compile(r"^\s*!bing\s*(.+)$")
        self.bard_prog = re.compile(r"^\s*!bard\s*(.+)$")
        self.pic_prog = re.compile(r"^\s*!pic\s*(.+)$")
        self.help_prog = re.compile(r"^\s*!help\s*.*$")
        self.talk_prog = re.compile(r"^\s*!talk\s*(.+)$")
        self.goon_prog = re.compile(r"^\s*!goon\s*.*$")
        self.new_prog = re.compile(r"^\s*!new\s*.*$")

    # close session
    def __del__(self) -> None:
        self.driver.disconnect()

    def login(self) -> None:
        self.driver.login()

    def pandora_init(self, user_id: str) -> None:
        self.pandora_data[user_id] = {
            "conversation_id": None,
            "parent_message_id": str(uuid.uuid4()),
            "first_time": True
        }
        
    async def run(self) -> None:
        await self.driver.init_websocket(self.websocket_handler)

    # websocket handler
    async def websocket_handler(self, message) -> None:
        print(message)
        response = json.loads(message)
        if "event" in response:
            event_type = response["event"]
            if event_type == "posted":
                raw_data = response["data"]["post"]
                raw_data_dict = json.loads(raw_data)
                user_id = raw_data_dict["user_id"]
                channel_id = raw_data_dict["channel_id"]
                sender_name = response["data"]["sender_name"]
                raw_message = raw_data_dict["message"]
                
                if user_id not in self.pandora_data:
                    self.pandora_init(user_id)

                try:
                    asyncio.create_task(
                        self.message_callback(
                            raw_message, channel_id, user_id, sender_name
                        )
                    )
                except Exception as e:
                    await asyncio.to_thread(self.send_message, channel_id, f"{e}")

    # message callback
    async def message_callback(
        self, raw_message: str, channel_id: str, user_id: str, sender_name: str
    ) -> None:
        # prevent command trigger loop
        if sender_name != self.username:
            message = raw_message

            if self.openai_api_key is not None:
                # !gpt command trigger handler
                if self.gpt_prog.match(message):
                    prompt = self.gpt_prog.match(message).group(1)
                    try:
                        response = await self.gpt(prompt)
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{response}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

                # !chat command trigger handler
                elif self.chat_prog.match(message):
                    prompt = self.chat_prog.match(message).group(1)
                    try:
                        response = await self.chat(prompt)
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{response}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

            if self.bing_api_endpoint is not None:
                # !bing command trigger handler
                if self.bing_prog.match(message):
                    prompt = self.bing_prog.match(message).group(1)
                    try:
                        response = await self.bingbot.ask_bing(prompt)
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{response}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

            if self.pandora_api_endpoint is not None:
                # !talk command trigger handler
                if self.talk_prog.match(message):
                    prompt = self.talk_prog.match(message).group(1)
                    try:
                        if self.pandora_data[user_id]["conversation_id"] is not None:
                            data = {
                                "prompt": prompt,
                                "model": self.pandora_api_model,
                                "parent_message_id": self.pandora_data[user_id]["parent_message_id"],
                                "conversation_id": self.pandora_data[user_id]["conversation_id"],
                                "stream": False,
                            }
                        else:
                            data = {
                                "prompt": prompt,
                                "model": self.pandora_api_model,
                                "parent_message_id": self.pandora_data[user_id]["parent_message_id"],
                                "stream": False,
                            }
                        response = await self.pandora.talk(data)
                        self.pandora_data[user_id]["conversation_id"] = response['conversation_id']
                        self.pandora_data[user_id]["parent_message_id"] = response['message']['id']
                        content = response['message']['content']['parts'][0]
                        if self.pandora_data[user_id]["first_time"]:
                            self.pandora_data[user_id]["first_time"] = False
                            data = {
                                "model": self.pandora_api_model,
                                "message_id": self.pandora_data[user_id]["parent_message_id"],
                            }
                            await self.pandora.gen_title(data, self.pandora_data[user_id]["conversation_id"])
                        
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{content}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)
                    
                # !goon command trigger handler
                if self.goon_prog.match(message) and self.pandora_data[user_id]["conversation_id"] is not None:
                    try:
                        data = {
                            "model": self.pandora_api_model,
                            "parent_message_id": self.pandora_data[user_id]["parent_message_id"],
                            "conversation_id": self.pandora_data[user_id]["conversation_id"],
                            "stream": False,
                        }
                        response = await self.pandora.goon(data)
                        self.pandora_data[user_id]["conversation_id"] = response['conversation_id']
                        self.pandora_data[user_id]["parent_message_id"] = response['message']['id']
                        content = response['message']['content']['parts'][0]
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{content}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

                # !new command trigger handler
                if self.new_prog.match(message):
                    self.pandora_init(user_id)
                    try:
                        await asyncio.to_thread(
                            self.send_message, channel_id, "New conversation created, please use !talk to start chatting!"
                        )
                    except Exception:
                        pass

            if self.bard_token is not None:
                # !bard command trigger handler
                if self.bard_prog.match(message):
                    prompt = self.bard_prog.match(message).group(1)
                    try:
                        # response is dict object
                        response = await self.bard(prompt)
                        content = str(response["content"]).strip()
                        await asyncio.to_thread(
                            self.send_message, channel_id, f"{content}"
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

            if self.bing_auth_cookie is not None:
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
                        await asyncio.to_thread(
                            self.send_file, channel_id, prompt, image_path
                        )
                    except Exception as e:
                        logger.error(e, exc_info=True)
                        raise Exception(e)

            # !help command trigger handler
            if self.help_prog.match(message):
                try:
                    await asyncio.to_thread(self.send_message, channel_id, self.help())
                except Exception as e:
                    logger.error(e, exc_info=True)

    # send message to room
    def send_message(self, channel_id: str, message: str) -> None:
        self.driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "message": message
            }
        )

    # send file to room
    def send_file(self, channel_id: str, message: str, filepath: str) -> None:
        filename = os.path.split(filepath)[-1]
        try:
            file_id = self.driver.files.upload_file(
                channel_id=channel_id,
                files={
                    "files": (filename, open(filepath, "rb")),
                },
            )["file_infos"][0]["id"]
        except Exception as e:
            logger.error(e, exc_info=True)
            raise Exception(e)

        try:
            self.driver.posts.create_post(
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

    # !gpt command function
    async def gpt(self, prompt: str) -> str:
        return await self.askgpt.oneTimeAsk(prompt)

    # !chat command function
    async def chat(self, prompt: str) -> str:
        return await self.chatbot.ask_async(prompt)

    # !bing command function
    async def bing(self, prompt: str) -> str:
        return await self.bingbot.ask_bing(prompt)

    # !bard command function
    async def bard(self, prompt: str) -> str:
        return await asyncio.to_thread(self.bardbot.ask, prompt)

    # !help command function
    def help(self) -> str:
        help_info = (
            "!gpt [content], generate response without context conversation\n"
            + "!chat [content], chat with context conversation\n"
            + "!bing [content], chat with context conversation powered by Bing AI\n"
            + "!bard [content], chat with Google's Bard\n"
            + "!pic [prompt], Image generation by Microsoft Bing\n"
            + "!talk [content], talk using chatgpt web\n"
            + "!goon, continue the incomplete conversation\n"
            + "!new, start a new conversation\n"
            + "!help, help message"
        )
        return help_info
