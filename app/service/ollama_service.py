import httpx
import json
import asyncio
from fastapi import Depends, HTTPException
from typing import List, AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import os

from app.models.chat import ChatModels
from app.models.chat import MessageModels
from app.models.ollama import OllamaRequest
from app.service.chat_service import ChatService, get_chat_service
# from app.service.message_service import MessageService, get_message_service
from app.service.message_service import MessageService, get_message_service
from app.service.rag_service import RAGService, get_rag_service
from app.setting.config import settings, get_settings
from app.setting.enum import DocsCollection


class OllamaService:
    def __init__(
        self,
        settings=Depends(get_settings),
        rag_service: RAGService = Depends(get_rag_service),
    ):
        self.base_url = settings.ollama_url
        self.timeout = settings.ollama_timeout
        self.rag_service = rag_service

    def count_tokens(self, text: str) -> int:
        # """Đếm số token trong văn bản sử dụng tokenizer"""
        # tokens = self.tokenizer.encode(text)
        # print(f"📝 Text: {text}\n🔢 Tokens: {len(tokens)}\n---")
        # return len(tokens)
        return len(text.split())

    async def check_model_exists(self, model_name: str) -> bool:
        try:
            # Lấy danh sách model từ API Ollama
            available_models = await self.list_models()
            for model in available_models:
                if model.get("name", None) == model_name:
                    return True

            return False
        except Exception as e:
            print(f"[ERROR] Không thể kiểm tra model '{model_name}': {str(e)}")
            # Trả về False để an toàn
            return False

    def combine_message_content(self, messages: List[Dict[str, str]]) -> str:
        """
        Combine all content from the messages into a single string.
        Args:
            messages (List[Dict[str, str]]): List of messages, each containing 'role' and 'content'.
        Returns:
            str: Combined content from all messages.
        """
        combined_content = " ".join(
            [message["content"] for message in messages if "content" in message]
        )
        return combined_content
    
    def get_current_query(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract the current user query from the messages.
        Args:
            messages (List[Dict[str, str]]): List of messages, each containing 'role' and 'content'.
        Returns:
            str: The content of the last user message.
        """
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""

    async def chat_stream(self, request: OllamaRequest) -> AsyncGenerator[str, None]:
        """
        Stream chat messages to Ollama API and yield responses.
        Args:
            request (OllamaRequest): The request object containing model and messages.
        Yields:
            str: JSON string of the response from Ollama API.
        """
        ollama_url = f"{self.base_url}/api/chat"
        model_to_use = request.model
        chat_id = 1;

        # Kiểm tra sự tồn tại của model
        if not await self.check_model_exists(model_to_use):
            error_message = f"Model '{model_to_use}' không tồn tại hoặc chưa được cài đặt trong Ollama"
            yield f"data: {json.dumps({'error': error_message})}\n\n"
            return

        # Combine content messages
        # text = self.combine_message_content(request.messages)
        query = self.get_current_query(request.messages)

        prompt = await self.rag_service.generate_prompt(query, DocsCollection.RAG)

        # load new message to context
        # for msg in messages:
        #     prompt.append({"role": "context", "content": msg.content})

        # Options for AI Model
        options = {
            "top_k": 64,
            "top_p": 0.95,
        }

        payload = {
            # "model": model_to_use,
            #TODO: set default
            "model": 'deepseek-r1:8b',
            "messages": prompt,
            "options": options,
            "stream": True,
        }

        print(f"[DEBUG] Full payload: {json.dumps(payload, ensure_ascii=False)}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", ollama_url, json=payload) as response:
                    if response.status_code != 200:
                        error_detail = await response.aread()
                        yield f"data: {json.dumps({'error': f'Ollama error: {error_detail}'})}\n\n"
                        return

                    # Stream response từ Ollama
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            try:
                                data = json.loads(chunk)
                                data["chat_id"] = chat_id
                                yield f"data: {json.dumps(data)}\n\n"

                            except json.JSONDecodeError:
                                # If chunk is not complete JSON, just send the raw text
                                yield f"data: {json.dumps({'text': chunk, 'chat_id': chat_id})}\n\n"

                yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'chat_id': chat_id})}\n\n"

    # Get List Ollama's Models
    async def list_models(self) -> List[str]:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500, detail=f"Ollama error: {response.text}"
                    )

                data = response.json()
                models = []
                models_data = data.get("models", [])

                for model in models_data:
                    info = {
                        "name": model.get("model", ""),
                        "displayName": model.get("name", ""),
                        "size": model.get("size", ""),
                        "modified": model.get("modified_at", ""),
                    }
                    models.append(info)
                return models
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Lỗi khi lấy danh sách model: {str(e)}"
            )


def get_ollama_service(
    settings=Depends(get_settings),
    rag_service=Depends(get_rag_service),
) -> OllamaService:
    return OllamaService(settings, rag_service)
