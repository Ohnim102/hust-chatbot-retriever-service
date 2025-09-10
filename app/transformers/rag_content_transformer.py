from pydantic import BaseModel
from typing import List, Dict, Any
from app.transformers.rag_file_transformer import transform_documents


def transform_to_content(documents: List[Any]) -> str:
    """
    Transform the context documents into a string format suitable for model input.

    Args:
        documents (List[Any]): List of documents to transform.

    Returns:
        str: Transformed string representation of the documents.
    """
    transformed_docs = transform_documents(documents)
    context_string = ""

    for doc in transformed_docs:
        write_source = False
        for idx, match in enumerate(doc["matches"]):
            if match.get("score", 0) < 0.54:
                continue
            if write_source == False:
                context_string += f"Nguồn tài liệu: {doc['source']}\n"
                context_string += f"Tiêu đề: {doc['metadata']['title']}\n"
                context_string += "Nội dung tài liệu:\n"
                write_source = True
            context_string += f"{match['page_content']} \n"

        context_string += "\n"

    return context_string.strip()
