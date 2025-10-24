import enum
from typing import *

import uuid
from pydantic import BaseModel, Field, model_validator
from fastapi import UploadFile

class SupportedFileTypes(enum.Enum):
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"
    XLSX = "xlsx"
    XLS = "xls"

    @classmethod
    def get_developed(cls):
        """get file types that are developed"""
        return [cls.DOCX.value, cls.DOC.value, cls.PDF.value]


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

    re_matcher: Optional[str] = Field(
        default=None,
        title="regular expression",
        description="[Advanced] general regular expression to match the separator(s)( which devides text chunks). Like '章节一', '第一条', 'A.1.1', etc."
    )
    "regular matcher, to match the separator to devide the text chunks"

    filename_in_chunk: bool = Field(
        default=False,
        title="filename_in_chunk",
        description="if you want to insert filename into chunks"
    )
    "if you want to insert filename into chunks"

    output_format: Literal["json","txt"] = Field(
        default="txt",
        title="output format", description="output format. support:['json', 'txt']")
    "otuput format you want. support:['json', 'txt']"

    @model_validator(mode="after")
    def check_file_type_validation(self) -> Self:
        supported_extensions = SupportedFileTypes.get_developed()
        file_extension = self.file.filename.rsplit(".",1)[-1]
        if file_extension not in supported_extensions:
            raise ValueError(
                "extension only support: supported_extensions. Yours: %s" % file_extension)
        return self


if __name__ == '__main__':
    x=ParsedFormData(request_id="etstresrtse")
    print(x)