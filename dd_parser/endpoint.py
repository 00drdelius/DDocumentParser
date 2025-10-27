import tempfile
from shutil import rmtree
from pathlib import Path
from contextlib import asynccontextmanager

import aiohttp

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from dd_parser.logg import logger
from dd_parser.config import TEMP_DIR, HTTP_CLIENT
from dd_parser.tools import async_wrapper, check_libreoffice
from dd_parser.schemas import SupportedFileTypes, ParsedFormData

app=FastAPI(
    title="DDocumentParser",
    description="document parser for parsing various complex documents into knowledge base",
    version="0.0.1",
    docs_url=None,
    redoc_url=None,
)


@asynccontextmanager
async def lifespan(app:FastAPI):
    global HTTP_CLIENT, TEMP_DIR
    check_libreoffice()
    HTTP_CLIENT = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False,),
        timeout=aiohttp.ClientTimeout(sock_connect=3.0,sock_read=300.0)
    )
    TEMP_DIR=Path(tempfile.mkdtemp(prefix="DDocumentParser_"))
    yield
    logger.info("[shuting down] remove duplicate components")
    await HTTP_CLIENT.close()
    await async_wrapper(rmtree, TEMP_DIR) #NOTE I should delete all files under temp_dir manually
    logger.info(f"[shuting down] temp_dir:({TEMP_DIR}) removed properly")
    await logger.complete()

@app.post(
    "/parse/",
    tags=["parser"],
    description=f"api to parse your document. Currently supported formats: {str(SupportedFileTypes.get_developed())}"
)
async def parse_api(form_data: ParsedFormData = Form(..., media_type="multipart/form-data")):
    logger.info(f"[request received] {form_data.request_id}")


