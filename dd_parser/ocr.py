import os
from typing import *

import aiohttp
from dotenv import load_dotenv

load_dotenv()
MINERU_URL = os.getenv("MINERU_URL")

async def request_mineru(
    http_client:aiohttp.ClientSession,
    request_id: str,
    output_format: Literal["json", "markdown"],
    file_stream:bytes,
    filename:str,
):
    formdata = aiohttp.FormData()
    formdata.add_field("file",file_stream,filename=filename,)
    formdata.add_field("request_id",request_id)
    formdata.add_field("output_format", output_format)
    async with http_client.post(MINERU_URL, data=formdata) as aresp:
        aresp.raise_for_status()
        data=aresp.json()
        return data
