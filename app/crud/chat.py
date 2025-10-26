from datetime import datetime
import logging
from typing import List
from sqlalchemy import select, update, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatModels
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.schemas.chat import Chat

logger = logging.getLogger("FastAPI:ChatCRUD")
logger.setLevel(logging.DEBUG)

class ChatCRUD:
    db_session = None

    def __init__(self, db_session: AsyncSession = None):
        self.db_session = db_session

    async def get_chats(self, page: int = 1, size: int = 10) -> List[ChatModels]:
        offset = (page - 1) * size
        stmt = (
            select(ChatModels)
            .order_by(ChatModels.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        result = await self.db_session.execute(stmt)
        chats = result.scalars().all()
        return chats
    
    async def create_chat(self, chat: Chat) -> Chat:
        stmt = insert(ChatModels).values(
            title=chat.title,
            description=chat.description,
            model=chat.model
        ).returning(ChatModels)
        
        try:
            result = await self.db_session.execute(stmt)
            logger.info(f"Chat created successfully: {result}")
            await self.db_session.commit()
            created_chat = result.fetchone()
            data = dict(created_chat._mapping)
            return data
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            await self.db_session.rollback()
            raise Exception(f"Error creating chat: {e}")
    
    async def update_chat(self, chat: Chat) -> Chat:
        stmt = update(ChatModels).where(ChatModels.id == chat.id).values(
            title=chat.title,
            description=chat.description,
            model=chat.model
        ) 
        try:
            result = await self.db_session.execute(stmt)
            logger.info(f"Chat updated successfully: {result}")
            await self.db_session.commit()
            return result
        except Exception as e:
            logger.error(f"Error updating chat: {e}")
            await self.db_session.rollback()
            raise Exception(f"Error updating chat: {e}")
    
    async def delete_chat(self, chat_id: int):
        stmt = delete(ChatModels).where(ChatModels.id == chat_id)
        try:
            result = await self.db_session.execute(stmt)
            logger.info(f"Chat deleted successfully: {result}")
            await self.db_session.commit()
            return result
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            await self.db_session.rollback()
            raise Exception(f"Error deleting chat: {e}")

    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatModels]:
        stmt = (
            select(ChatModels)
            .options(selectinload(ChatModels.messages))
            .where(ChatModels.id == chat_id)
        )
        result = await self.db_session.execute(stmt)
        chat = result.scalar_one_or_none()
        return chat
