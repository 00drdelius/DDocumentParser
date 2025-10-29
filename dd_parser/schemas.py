import enum
import uuid
from typing import *

from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator
from fastapi import UploadFile

class SupportedFileTypes(enum.Enum):
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"
    MD = "md"
    TXT = "txt"
    XLSX = "xlsx"
    XLS = "xls"

    @classmethod
    def get_developed(cls):
        """get file types that are developed"""
        return [cls.DOCX.value, cls.DOC.value, cls.PDF.value, cls.MD.value, cls.TXT.value]


OutputFormat:TypeAlias = Literal["json","txt"]

class ParsedFormData(BaseModel):
    request_id: Optional[str] = Field(
        default_factory=lambda :str(uuid.uuid4()),
        title="request id",
        description="[Optional] request id, to mark the request.")
    "[Optional] request id, to mark the request."

    file: UploadFile = Field(
        ...,
        title="upload file",
        description="upload the file needs to be parsed")
    "upload the file needs to be parsed"

    re_matchers: Optional[List[str]] = Field(
        default=None,
        title="regular expression",
        description=(
            "[Advanced] general regular expression to match the separator(s)( which devides text chunks).\n\n"
            "Like '章节一', '第一条', 'A.1.1', etc.\n\n"
            "Also you could upload multi expressions to split text with, like, '第一章', '第一章...第一条', etc."
        )
    )
    "regular matcher(s), to match the separator to devide the text chunks"

    filename_in_chunk: bool = Field(
        default=False,
        title="filename_in_chunk",
        description="if you want to insert filename into chunks"
    )
    "if you want to insert filename into chunks"

    output_format: OutputFormat = Field(
        default="txt",
        title="output format", description="output format. support:['json', 'txt']")
    "otuput format you want. support:['json', 'txt']"

    length_limit: Optional[int] = Field(
        title="length limit",
        description="max length in a chunk. Every length of chunk <= length_limit. **Only used when `output_format==txt`**",)
    "max length in a chunk. Every length of chunk <= length_limit. **Only used when `output_format==txt`**"

    chunk_splitter: str = Field(
        default="\n\n\n\n",
        title="chunk splitter",
        description="Text splitter for separating content. Default is `\\n\\n\\n\\n`.  **Only used when `output_format==txt`**",)
    "Text splitter for separating content. Default is `\\n\\n\\n\\n`.  **Only used when `output_format==txt`**"

    @model_validator(mode="after")
    def check_file_type_validation(self) -> Self: #NOTE `typing.Self` only applied in python311 or higher
        supported_extensions = SupportedFileTypes.get_developed()
        file_extension = self.file.filename.rsplit(".",1)[-1]
        if file_extension not in supported_extensions:
            raise ValueError(
                "extension only support: supported_extensions. Yours: %s" % file_extension)
        return self


if __name__ == '__main__':
    x=ParsedFormData(request_id="etstresrtse")
    print(x)