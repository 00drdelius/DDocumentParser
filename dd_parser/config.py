import os
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEMP_DIR:Path = None
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
MINERU_URL = os.getenv("MINERU_URL", None)

HTTP_CLIENT:aiohttp.ClientSession = None
