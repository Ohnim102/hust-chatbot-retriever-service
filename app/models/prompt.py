from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class OllamaMessage(BaseModel):
    role: str
    message: str

class OllamaPrompt(BaseModel):
    prompt: List[OllamaMessage]

# Ví dụ về dữ liệu
example_prompt = OllamaPrompt(
    prompt=[
        OllamaMessage(role="user", message="Chào, tôi cần hỗ trợ."),
        OllamaMessage(role="assistant", message="Chào bạn! Tôi có thể giúp gì cho bạn?"),
    ]
)
