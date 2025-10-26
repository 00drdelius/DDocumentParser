from typing import *
import regex as re
from pathlib import Path

from aiofiles import open as aopen

from dd_parser.logg import logger
from dd_parser.config import TEMP_DIR
from dd_parser.schemas import ParsedFormData
from dd_parser.tools import (
    async_wrapper,
    get_pure_docx_text,
    aconvert_docs_to_docxs,
    request_mineru,
)
savebytes_dir = TEMP_DIR / "save_bytes"
doc_converted_dir = TEMP_DIR / "doc_converted"
savebytes_dir.mkdir(exist_ok=False)
doc_converted_dir.mkdir(exist_ok=False)


regex_patterns = {
    #NOTE 第一章  第一条。。。
    "chapters_with_articles": dict(
        chapter_pattern = re.compile(r"^第[一二三四五六七八九十百]+\s{0,1}章[^\n]*"),
        article_pattern = re.compile(r"^第[一二三四五六七八九十百]+\s{0,1}条[^\n]*"),
        example = "第一章  第一条。。。",
    ),
    #NOTE 第一条  （一）。。。
    "articles_with_parentheses": dict(
        chapter_pattern = re.compile(r"^第[一二三四五六七八九十百]+\s{0,1}条\s{0,1}[^\n]*"),
        article_pattern = re.compile(r"^[（(][一二三四五六七八九十百]*?[）)][^\n]*"),
        example = "第一条  （一）。。。",
    ),
    #NOTE 一、  （一）。。。
    "chinese_dots_with_articles": dict(
        chapter_pattern = re.compile(r"^[一二三四五六七八九十百]+\s{0,1}、[^\n]*"),
        article_pattern = re.compile(r"^[（(][一二三四五六七八九十百]*?[）)][^\n]*"),
        example = "一、  （一）。。。",
    ),
}


def get_regex_pattern(pure_text: str) -> tuple[Optional[re.Pattern], Optional[re.Pattern]] | re.Pattern:
    """
    get regex pattern by matching the text with predefined patterns.
    Args:
        pure_text (str): The pure text extracted from the document
    Returns:
        tuple[re.Pattern, re.Pattern]: The matched regex patterns for chapter and article
    """
    single_pattern:re.Pattern = None #NOTE single pattern detects text only with single pattern matched
    lines = pure_text.splitlines()

    for key, patterns in regex_patterns.items():
        chapter_pattern = patterns["chapter_pattern"]
        article_pattern = patterns["article_pattern"]
        round_chapter_pattern_detected = False
        round_article_pattern_detected = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if chapter_pattern.search(line):
                round_chapter_pattern_detected = True
                if not single_pattern:
                    #NOTE single pattern can only be assigned once.
                    # If both patterns are detected in the same round, it returns and only returns both patterns
                    single_pattern = chapter_pattern

            if article_pattern.search(line):
                round_article_pattern_detected = True
                if not single_pattern:
                    single_pattern = article_pattern

            if round_chapter_pattern_detected and round_article_pattern_detected:
                #NOTE if both patterns are detected in the same round, we consider it a match
                print(f"Detected pattern: {key} ( {patterns['example']} )")
                return chapter_pattern, article_pattern

        # reset for next line
        round_chapter_pattern_detected, round_article_pattern_detected = False, False

    if single_pattern:
        print("Detected single pattern only, returning single pattern")
        return single_pattern

    print("No matching pattern found.")
    return None, None


def single_pattern_preprocess(
    pure_text:str,
    chapter_pattern:re.Pattern,
) -> list[dict[str,str]]:
    """
    Preprocess file to extract chapters by single pattern

    Example:
        This function process files with chapters formatted like:
        ```
        ...
        第一章 预算管理
        为了加强预算管理，规范预算行为，依据《中华人民共和国预算法》等法律法规，结合本单位实际，制定本制度。
        
        第二章 采购管理
        预算管理应遵循合法性、真实性、完整性、准确性和及时性的原则。
        ...
        ```
    Args:
        pure_text (str): The pure text extracted from the document
        chapter_pattern (re.Pattern): The regex pattern for chapter
    """
    slices = []
    lines = pure_text.splitlines()
    buffer = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if chapter_pattern.search(line):
            if buffer:
                slices.append({
                    "chapter": "",
                    "article": "",
                    "content": "\n".join(buffer)
                })
                buffer = []
            buffer.append(line)
        else:
            buffer.append(line)

    #TODO save the last buffer if exists
    if buffer:
        slices.append({
            "chapter": "",
            "article": "",
            "content": "\n".join(buffer)
        })
    return slices


def double_patterns_preprocess(
    pure_text:str,
    chapter_pattern:re.Pattern,
    article_pattern:re.Pattern,
) -> list[dict[str,str]]:
    """
    Preprocess file to extract chapters and articles by parent and child patterns.

    Example:
        This function process files with chapters and articles formatted like:
        ```
        ...
        第一章 预算管理
        第一条
        为了加强预算管理，规范预算行为，依据《中华人民共和国预算法》等法律法规，结合本单位实际，制定本制度。
        
        第二条
        预算管理应遵循合法性、真实性、完整性、准确性和及时性的原则。
        ...

        第二章 采购管理
        ...
        ```
    Args:
        pure_text (str): The pure text extracted from the document
        chapter_pattern (re.Pattern): The regex pattern for chapter
        article_pattern (re.Pattern): The regex pattern for article
    """
    lines = pure_text.splitlines()
    last_chapter = ""
    last_article = None
    buffer = []
    slices = []

    print("start processing chapters and articles...")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # encounter new chapter
        if chapter_pattern.search(line):
            if buffer and not last_article:
                #NOTE The content before the first chapter,
                # or the content between chapters without articles, which belongs to the last chapter
                slices.append({
                    "chapter": last_chapter,
                    "article": "",
                    "content": "\n".join(buffer)
                })
                buffer = []

            elif last_article and buffer:
                #NOTE You must save the last article before starting a new chapter
                # otherwise the last article will be saved with the new chapter
                slices.append({
                    "chapter": last_chapter,
                    "article": last_article,
                    "content": "\n".join(buffer)
                })
                last_article = None
                buffer = []

            elif last_chapter and not buffer and not last_article:
                #NOTE If there is no content between chapters, 
                # or content and last chapter are on the same line
                slices.append({
                    "chapter": last_chapter,
                    "article": "",
                    "content": ""
                })
            last_chapter = line
            continue

        # encounter new article
        if article_pattern.search(line):
            if last_article and buffer:
                slices.append({
                    "chapter": last_chapter,
                    "article": last_article,
                    "content": "\n".join(buffer)
                })
            last_article = line
            buffer = [line]
        else:
            buffer.append(line)

    #NOTE save the last article if exists and mostly exists
    # or the content after the last article
    if last_article or buffer:
        slices.append({
            "chapter": last_chapter,
            "article": last_article,
            "content": "\n".join(buffer)
        })
    return slices


async def preprocess_before_chunk(formdata: ParsedFormData):
    filename = formdata.file.filename
    file_stream = await formdata.file.read()
    temp_filepath = savebytes_dir / filename
    async with aopen(str(temp_filepath), "wb") as awf:
        await awf.write(file_stream)
    match temp_filepath.suffix:
        case ".docx":
            text = await async_wrapper(get_pure_docx_text, temp_filepath)
        case ".doc":
            temp_store_docxs_dir = doc_converted_dir / formdata.request_id
            await async_wrapper(temp_store_docxs_dir.mkdir, exist_ok=True, parents=False)
            filepaths = await aconvert_docs_to_docxs(temp_filepath, temp_store_docxs_dir)
            text = await async_wrapper(get_pure_docx_text, filepaths[0])
        case ".pdf":
            text = await request_mineru(
                request_id=formdata.request_id,
                output_format="markdown",
                file_stream=file_stream,
                filename=filename)
        case _:
            raise ValueError(f"Unsupported file format: {filename}")
    patterns = formdata.re_matchers
    if not patterns:
        patterns = get_regex_pattern(text)
    elif isinstance(patterns, str):
        patterns = re.compile(patterns)
    elif isinstance(patterns, list):
        patterns = [re.compile(i) for i in patterns]

    if isinstance(patterns, re.Pattern):
        print("✅ Detected only single pattern, jump to single patterns preprocess...")
        slices = single_pattern_preprocess(text, patterns)
    elif isinstance(patterns, List, Tuple):
        chapter_pattern, article_pattern = patterns
        if not chapter_pattern or not article_pattern:
            print("❌ No matching chapter/article pattern found, returns the whole text as a single chunk.")
            slices = [{
                "chapter": "",
                "article": "",
                "content": text
            }]
        else:
            print("✅ Detected both chapter and article patterns, jump to double patterns preprocess...")
            slices = double_patterns_preprocess(
                pure_text=text,
                chapter_pattern=chapter_pattern,
                article_pattern=article_pattern
            )

    logger.info(f"✅ [preprocessing done] {len(slices)} chunks in total")
    # txt_slices=splitter.join([f"{filename}\n{slice['chapter']}\n{slice['content']}" for slice in slices])
    output_format = formdata.output_format
    filename_in_chunk = formdata.filename_in_chunk
    length_limit = formdata.length_limit
    splitter = formdata.chunk_splitter

    if output_format == "txt":
        # write to txt file
        formated_text = ""
        written_line=""
        for slice in slices:
            if filename_in_chunk:
                line = f"{filename}\n{slice['chapter']}\n{slice['content']}\n"
            else:
                line = f"{slice['chapter']}\n{slice['content']}\n"

            if length_limit:
                if len(written_line+line)<=length_limit:
                    written_line+=line
                else:
                    formated_text+=written_line+splitter
                    written_line=line
            else:
                formated_text+=line+splitter
        if length_limit:
            #NOTE write into file for the last part && if whole document length < length_limit
            formated_text+=written_line
        return slices

    return slices
    

    