from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import httpx
import json
from typing import List, Optional

from app.models.ollama import OllamaRequest
from app.service.ollama_service import OllamaService, get_ollama_service
from app.setting.config import settings

router = APIRouter(prefix="/ollama", tags=["ollama"])


@router.post("/chat/stream")
async def chat_stream(
    request: OllamaRequest,
    ollama_service: OllamaService = Depends(get_ollama_service),
):
    return StreamingResponse(
        ollama_service.chat_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/models")
async def get_models(ollama_service: OllamaService = Depends(get_ollama_service)):
    return await ollama_service.list_models()
