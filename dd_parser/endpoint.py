import aiohttp
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

app=FastAPI(
    title="DDocumentParser",
    description="document parser for parsing various complex documents into knowledge base",
    version="0.0.1",
    docs_url=None,
    redoc_url=None,
)

http_client:aiohttp.ClientSession = None

@asynccontextmanager
async def lifespan(app:FastAPI):
    global http_client
    http_client = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False,),
        timeout=aiohttp.ClientTimeout(sock_connect=3.0,sock_read=300.0)
    )
    yield
    await http_client.close()


@app.post(
    "/parse/",
    tags=["parser"],
    description="api to parse your document"
)
async def parse_api(
    file: UploadFile = File(
        ...,
        title="parsing file",
        description=f"file to parse. Currently support "
    )
):
    ...
