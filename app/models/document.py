from pydantic import BaseModel
from typing import Optional, Dict, Any


class Document(BaseModel):
    page_content: str
    # metadata is a dict of arbitrary keys. We add an optional document_id
    # to be able to group chunks belonging to the same source document.
    metadata: Dict[str, Any] = {}
    document_id: Optional[str] = None
    type: str = "Document"


class LoadDocumentRequest(BaseModel):
    file: bytes
    metadata: Dict[str, Any] = {}

