import aiohttp
import asyncio
import json

from log import getlogger

logger = getlogger()


class askGPT:
    def __init__(
        self, session: aiohttp.ClientSession, headers: str
    ) -> None:
        self.session = session
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        self.headers = headers

    async def oneTimeAsk(self, prompt: str) -> str:
        jsons = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
        max_try = 2
        while max_try > 0:
            try:
                async with self.session.post(
                    url=self.api_endpoint, json=jsons, headers=self.headers, timeout=120
                ) as response:
                    status_code = response.status
                    if not status_code == 200:
                        # print failed reason
                        logger.warning(str(response.reason))
                        max_try = max_try - 1
                        # wait 2s
                        await asyncio.sleep(2)
                        continue

                    resp = await response.read()
                    return json.loads(resp)["choices"][0]["message"]["content"]
            except Exception as e:
                raise Exception(e)
