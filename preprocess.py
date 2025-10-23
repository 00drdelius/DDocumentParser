from typing import Literal, Optional
from pathlib import Path
import regex as re
import json
from tools import get_pure_text, convert_docs_to_docxs
import tempfile


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


def preprocess_before_chunk(
    filepath:str,
    output_format:Literal['json','txt']="txt",
    output_filepath:str="output.txt",
    splitter:str="\n\n\n\n",
    filename_in_chunk:str=True,
    length_limit:int=None,
):
    """
    Preprocess file and save the structured data in a given file format, before chunking.

    Args:
        filepath (str): Path to the input file
        output_format (Literal['json', 'txt']): Output format, either 'json' or 'txt'. Default is 'txt'
        output_filepath (str): Path to the output file. Default is "output.txt" under the current working directory
        splitter (str): Text splitter for separating content. Default is `\\n\\n\\n\\n`.  **Only used when `output_format==txt`**
        filename_in_chunk(bool): if True, set filename at the beginning of every chunk when output_format=='txt'
        length_limit(int): max length in a chunk. Every length of chunk <= length_limit. **Only used when `output_format==txt`**
    """
    match filepath.lower().split('.')[-1]:
        case "pdf"|"docx":
            # extract pure text
            text = get_pure_text(filepath)
        case "doc":
            print("Detect doc file. Converting .doc to .docx using LibreOffice first...")
            with tempfile.TemporaryDirectory(prefix="preprocess_docx_",delete=True) as tmpdirname:
                filename = Path(filepath).stem + ".docx" #NOTE .stem get filename without suffix
                convert_docs_to_docxs(filepath, output_directory=tmpdirname)
                filepath = str(Path(tmpdirname) / filename)
                # extract pure text
                text = get_pure_text(filepath)
        case _:
            raise ValueError(f"Unsupported file format: {filepath}")

    # detect regex pattern
    maybe_patterns = get_regex_pattern(text)
    if isinstance(maybe_patterns, re.Pattern):
        print("✅ Detected only single pattern, jump to single patterns preprocess...")
        slices = single_pattern_preprocess(text, maybe_patterns)
    elif isinstance(maybe_patterns, tuple):
        chapter_pattern, article_pattern = maybe_patterns
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


    print(f"✅ preprocessing done: {output_filepath} ( {len(slices)} chunks in total )")
    # txt_slices=splitter.join([f"{filename}\n{slice['chapter']}\n{slice['content']}" for slice in slices])

    if output_format == "txt":
        filename=""
        if filename_in_chunk: filename = Path(output_filepath).stem
        with open(output_filepath, "w", encoding="utf-8") as f:
            # write to txt file
            written_line=""
            for slice in slices:
                line = f"{filename}\n{slice['chapter']}\n{slice['content']}\n"
                if length_limit:
                    if len(written_line+line)<=length_limit:
                        written_line+=line
                    else:
                        f.write(written_line+splitter)
                        written_line=line
                else:
                    f.write(line+splitter)
            if length_limit:
                #NOTE write into file for the last part && if whole document length < length_limit
                f.write(written_line)
        return slices
    elif output_format == "json":
        # write to JSON file
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(slices, f, ensure_ascii=False, indent=2)

    return slices


def test_batch():
    input_directory = Path(r"审计规章制度(docx)")
    for input_file in input_directory.glob("*"):
        print("addressing file:", input_file.name)
        preprocess_before_chunk(str(input_file.absolute()), output_format="json", output_filepath=f"output_{input_file.stem}.json")

def test_single():
    input_file=Path(r"审计规章制度\关于印发《中山市审计局审计业务电子数据管理办法》的通知_已签章_V0(1).pdf")
    preprocess_before_chunk(str(input_file.absolute()), output_format="txt", output_filepath=f"{input_file.stem}.txt")

def main():
    files_dir = Path(r"审计规章制度")
    output_dir = Path(r"splitted_by_articles")
    for file in files_dir.glob("*"):
        print("addressing file:", file.name)
        output_filepath = output_dir / f"{file.stem}.txt"
        try:
            preprocess_before_chunk(
                str(file.absolute()), output_format="txt", output_filepath=output_filepath,
                filename_in_chunk=True
            )
        except Exception as e:
            print(f"Error processing file {file.name}: {e}")
            print("continue to next file...")
            continue

def main2():
    "another devision by max length."
    files_dir = Path(r"审计规章制度")
    output_dir = Path(r"splitted_by_articles_tokens")
    for file in files_dir.glob("*"):
        print("addressing file:", file.name)
        output_filepath = output_dir / f"{file.stem}.txt"
        try:
            preprocess_before_chunk(
                str(file.absolute()), output_format="txt", output_filepath=output_filepath,
                filename_in_chunk=True,
                length_limit=4000,
            )
        except Exception as e:
            print(f"Error processing file {file.name}: {e}")
            print("continue to next file...")
            continue

if __name__ == "__main__":
    # main()
    main2()
    # test_single()
