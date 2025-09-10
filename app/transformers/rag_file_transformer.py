from pydantic import BaseModel
from typing import List, Dict, Any
from collections import defaultdict

class Metadata(BaseModel):
    source: str
    total_pages: int
    creationdate: str
    title: str
    author: str

class Document(BaseModel):
    id: str
    metadata: Metadata
    page_content: str
    type: str

class TransformedDocument(BaseModel):
    source: str
    metadata: Metadata
    matches: List[Dict[str, Any]]

def transform_documents(documents: List[Any]) -> List[TransformedDocument]:
    response_documents = []
    # Duyệt qua danh sách tài liệu và nhóm theo source
    for raw_doc in documents:
        doc = raw_doc[0]
        score = raw_doc[1]

        metadata = doc.metadata
        source = metadata.get("source", "unknown_source")

        new_metadata = {
            "source": source,
            "total_pages": metadata.get("total_pages", 0),
            "creationdate": metadata.get("creationdate", ""),
            "title": metadata.get("title", "Untitled"),
            "author": metadata.get("author", "Unknown Author"),
        }

        existing_match_index = None
        for index, match in enumerate(response_documents):
            match_metadata = match.get('metadata', {})
            if match_metadata.get('source') == source:
                existing_match_index = index
                break

        if existing_match_index is not None:
            response_documents[existing_match_index]['matches'].append({
                "page_content": doc.page_content,
                "score": score,
                "page": metadata.get("page", 0),
            })
        else:
            response_documents.append({
                "source": source,
                "metadata": new_metadata,
                "matches": [{
                    "page_content": doc.page_content,
                    "score": score,
                    "page": metadata.get("page", 0),
                }]
            })
        
    return response_documents
