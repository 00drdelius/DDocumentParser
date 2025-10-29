import os
import sys

from loguru import logger

from .config import LOG_LEVEL

folder_ = "./log/"
rotation_ = "10 MB"
retention_ = "30 days"
encoding_ = "utf-8"
backtrace_ = True
diagnose_ = True

logger.remove() #NOTE remove all preset logger
# 格式里面添加了process和thread记录，方便查看多进程和线程程序
format_ = (
'<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> '
# '| <magenta>{process}</magenta>:<yellow>{thread}</yellow> ' #NOTE 
'| <cyan>{file}</cyan>:<yellow>{line}</yellow>@<cyan>{function}</cyan> - <level>{message}</level>'
) #NOTE {file}:{line}@{function} allows you to directly trace back to the executing line in vscode.


logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format=format_,
    colorize=True,
    backtrace=backtrace_, diagnose=diagnose_,
    # filter=lambda record: record["level"].no >= logger.level("CRITICAL").no
)

logger.add(
    folder_+"logs/app_{time:YYYY-MM-DD}.log",
    level=LOG_LEVEL,
    format=format_,
    colorize=False, #NOTE logging into file cannot set color. You don't want your log file contains text like `[32m2025-10-26 12:58:59[0m ``
    backtrace=backtrace_, diagnose=diagnose_,
    enqueue=True, #NOTE to avoid logging everywhere in multi processing or asyncio program.
    encoding=encoding_,
    rotation=rotation_,retention=retention_,
)