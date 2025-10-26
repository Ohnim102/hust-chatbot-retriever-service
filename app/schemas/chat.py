from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Message(BaseModel):
    id: int
    role: str
    content: str
    tokens: Optional[int]
    model: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        validate_by_name = True

class Chat(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    model: Optional[str] = None
    messages: Optional[List[Message]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
       from_attributes = True

class MessageCreate(BaseModel):
    role: str
    content: str
    tokens: Optional[int] = None
    model: Optional[str] = None
