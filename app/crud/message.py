from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import MessageModels
from app.schemas.chat import Message
from datetime import datetime


class MessageCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_messages_by_chat_id(self, chat_id: int, page: int = 1, size: int = 50) -> List[Message]:
        skip = (page - 1) * size
        query = select(MessageModels).where(MessageModels.chat_id == chat_id).order_by(MessageModels.id).offset(skip).limit(size)
        result = await self.db.execute(query)
        return [Message.from_orm(msg) for msg in result.scalars().all()]
    
    async def create_message(self, chat_id: int, message: Message) -> Message:
        db_message = MessageModels(
            chat_id=chat_id,
            role=message.role,
            content=message.content,
            tokens=message.tokens,
            model=message.model
        )
        self.db.add(db_message)
        await self.db.commit()
        await self.db.refresh(db_message)
        return Message.from_orm(db_message)
    
    async def update_message(self, message_id: int, content: str) -> Message:
        query = select(MessageModels).where(MessageModels.id == message_id)
        result = await self.db.execute(query)
        db_message = result.scalar_one_or_none()
        
        if db_message:
            db_message.content = content
            await self.db.commit()
            await self.db.refresh(db_message)
            return Message.from_orm(db_message)
        return None
    
    async def delete_message(self, message_id: int) -> None:
        query = select(MessageModels).where(MessageModels.id == message_id)
        result = await self.db.execute(query)
        db_message = result.scalar_one_or_none()
        
        if db_message:
            await self.db.delete(db_message)
            await self.db.commit()
    
    async def get_last_messages(self, chat_id: int, count: int = 10) -> List[Message]:
        query = select(MessageModels).where(MessageModels.chat_id == chat_id).order_by(desc(MessageModels.id)).limit(count)
        result = await self.db.execute(query)
        messages = [Message.from_orm(msg) for msg in result.scalars().all()]
        return list(reversed(messages)) 
    
    async def count_messages(self, chat_id: int) -> int:
        query = select(MessageModels).where(MessageModels.chat_id == chat_id)
        result = await self.db.execute(query)
        return len(result.scalars().all())
