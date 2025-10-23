import enum

class SupportedFileTypes(enum.Enum):
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"
    XLSX = "xlsx"
    XLS = "xls"

    @classmethod
    def get_developed(cls):
        """get file types that are developed"""
        return [cls.DOCX, cls.DOC, cls.PDF]

