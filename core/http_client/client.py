import asyncio
from socket import AF_INET
from typing import Any, List, Optional

import aiohttp
import orjson

from core.fastapi.response.custom_response import json_encoder_extend

SIZE_POOL_AIOHTTP = 100
CLIENT_TIME_OUT = 2


class Aiohttp:
    sem: Optional[asyncio.Semaphore] = None
    aiohttp_client: Optional[aiohttp.ClientSession] = None

    @classmethod
    def get_aiohttp_client(cls) -> aiohttp.ClientSession:
        if cls.aiohttp_client is None:
            timeout = aiohttp.ClientTimeout(total=CLIENT_TIME_OUT)
            connector = aiohttp.TCPConnector(
                family=AF_INET, limit_per_host=SIZE_POOL_AIOHTTP
            )
            cls.aiohttp_client = aiohttp.ClientSession(
                timeout=timeout, connector=connector
            )

        return cls.aiohttp_client

    @classmethod
    async def close_aiohttp_client(cls) -> None:
        if cls.aiohttp_client:
            await cls.aiohttp_client.close()
            cls.aiohttp_client = None

    @classmethod
    async def query_url(
        cls, url: str, headers: dict = None, data=None, result_type="json"
    ) -> Any:
        client = cls.get_aiohttp_client()
        if data is not None:
            data = orjson.dumps(data, default=json_encoder_extend)
        try:
            async with client.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    return {"ERROR OCCURED" + str(await response.text())}
                if result_type == "json":
                    result = await response.json()
                elif result_type == "text":
                    result = await response.text()
                else:
                    result = await response.text()
        except Exception as e:
            return {"ERROR": e}
        return result

    @staticmethod
    async def on_start_up() -> None:
        Aiohttp.get_aiohttp_client()

    @staticmethod
    async def on_shutdown() -> None:
        await Aiohttp.close_aiohttp_client()
