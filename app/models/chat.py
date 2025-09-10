from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base


class ChatModels(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # back_populates helps with two-way connection, and cascade is so that when a chat is deleted,
    #  all child messages are also deleted.
    messages = relationship("MessageModels", back_populates="chat", cascade="all, delete-orphan")
    def __init__(self, title: str, model: str, description: str = None):
        self.title = title
        self.model = model
        self.description = description

    def __repr__(self) -> str:
        return f"<ChatModels(id={self.id}, title={self.title}, model={self.model}, description={self.description})>"


class MessageModels(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    # chat_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)   

    # Create relationship to ChatModels
    chat = relationship("ChatModels", back_populates="messages")

    def __init__(self, chat_id: int, role: str, content: str, tokens: int = None, model: str = None):
        self.chat_id = chat_id
        self.role = role
        self.content = content
        self.tokens = tokens
        self.model = model

    def __repr__(self) -> str:
        return f"<MessageModels(id={self.id}, role={self.role}, content={self.content}, tokens={self.tokens}, role={self.role}, model={self.model})>"
