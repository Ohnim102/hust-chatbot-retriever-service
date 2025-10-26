import os
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.params import Depends
from app.service.rag_service import RAGService, get_rag_service
from app.setting.enum import DocsCollection

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/upload-for-search")
async def load_document(
    file: Annotated[UploadFile, File()],
    rag_service: RAGService = Depends(get_rag_service),
):
    upload_directory = "./temp_uploads"
    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(upload_directory, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    documents = await rag_service.load_and_split_document(
        file_path,
        DocsCollection.SEARCH,
    )
    return documents

@router.post("/upload-for-rag")
async def load_document(
    file: Annotated[UploadFile, File()],
    rag_service: RAGService = Depends(get_rag_service),
):
    upload_directory = "./temp_uploads"
    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(upload_directory, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    documents = await rag_service.load_and_split_document(
        file_path,
        DocsCollection.RAG,
        {
            "chunk_size": 2000,
            "chunk_overlap": 150,
        },
    )
    return documents

@router.delete("/delete-document-by-doc-id/{doc_id}")
async def delete_documents_by_doc_id(
    doc_id: str,
    collection: DocsCollection = DocsCollection.RAG,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Delete documents by document id.

    Use the path parameter `doc_id` to specify which document to delete.
    The `collection` may be passed as a query parameter (defaults to SEARCH).
    """
    result = await rag_service.delete_documents_by_doc_id(doc_id, collection)
    return {"success": bool(result), "doc_id": doc_id}

@router.get("/query")
async def query_document(
    query: str,
    k: int,
    collection: DocsCollection = DocsCollection.SEARCH,
    rag_service: RAGService = Depends(get_rag_service),
):
    return await rag_service.query_document(collection, query, k)


@router.get("/generate-prompt")
async def query_document(
    query: str,
    collection: DocsCollection = DocsCollection.SEARCH,
    rag_service: RAGService = Depends(get_rag_service),
):
    return await rag_service.generate_prompt(query, collection)


@router.get("/clear-vectordb")
async def clear_vectordb(
    collection: DocsCollection,
    rag_service: RAGService = Depends(get_rag_service),
):
    return await rag_service.clear_vectordb(collection)

