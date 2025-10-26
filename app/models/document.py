from pydantic import BaseModel

class Document(BaseModel):
    page_content: str
    metadata: object = {}
    type: str = "Document"

class LoadDocumentRequest(BaseModel):
    file: bytes
    metadata: object = {}

