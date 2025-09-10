import os
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.params import Depends
from app.service.rag_service import RAGService, get_rag_service
from app.setting.enum import DocsCollection

router = APIRouter(prefix="/rag", tags=["loag"])

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


@router.get("/query")
async def query_document(
    query: str,
    k: int,
    collection: DocsCollection = DocsCollection.SEARCH,
    rag_service: RAGService = Depends(get_rag_service),
):
    return await rag_service.query_document(collection, query, k)


@router.get("/clear-vectordb")
async def clear_vectordb(
    collection: DocsCollection,
    rag_service: RAGService = Depends(get_rag_service),
):
    return await rag_service.clear_vectordb(collection)

