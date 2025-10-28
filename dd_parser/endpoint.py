from shutil import rmtree
from pathlib import Path
from contextlib import asynccontextmanager

import aiohttp

from fastapi import APIRouter, Form

from .logg import logger
from .config import HTTP_CLIENT, TEMP_DIR
from .tools import async_wrapper, acheck_libreoffice
from .schemas import SupportedFileTypes, ParsedFormData
from .parse import preprocess_before_chunk


@asynccontextmanager
async def lifespan(app:APIRouter):
    global HTTP_CLIENT
    logger.info("[dd_parser api] start")
    await acheck_libreoffice()
    HTTP_CLIENT = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False,),
        timeout=aiohttp.ClientTimeout(sock_connect=3.0,sock_read=300.0)
    )
    yield
    logger.info("[shuting down] remove duplicate components")
    await HTTP_CLIENT.close()
    await async_wrapper(rmtree, TEMP_DIR) #NOTE I should delete all files under temp_dir manually
    logger.info(f"[shuting down] temp_dir:({TEMP_DIR}) removed properly")
    await logger.complete()

router=APIRouter(
    tags=["dd_parser"],
    lifespan=lifespan)

@router.post(
    "/parse/",
    description=f"api to parse your document. Currently supported formats: {str(SupportedFileTypes.get_developed())}"
)
async def parse_api(
    form_data: ParsedFormData = Form(..., media_type="multipart/form-data")):

    logger.info(f"[request received] {form_data.request_id}")
    slices = await preprocess_before_chunk(form_data)
    return slices
