from typing import List, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.dependencies import get_db
from app.schemas.chat import Message
from app.crud.message import MessageCRUD

class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_crud = MessageCRUD(self.db)
    
    async def get_messages_by_chat_id(self, chat_id: int, page: int = 1, size: int = 50) -> List[Message]:
        messages = await self.message_crud.get_messages_by_chat_id(chat_id, page, size)
        return messages
    
    async def add_message(self, chat_id: int, message: Message) -> Message:
        new_message = await self.message_crud.create_message(chat_id, message)
        return new_message
    
    async def update_message(self, message_id: int, content: str) -> Message:
        updated_message = await self.message_crud.update_message(message_id, content)
        return updated_message
    
    async def delete_message(self, message_id: int) -> None:
        await self.message_crud.delete_message(message_id)
    
    async def get_last_messages(self, chat_id: int, count: int = 10) -> List[Message]:
        messages = await self.message_crud.get_last_messages(chat_id, count)
        return messages
    
    async def count_messages(self, chat_id: int) -> int:
        count = await self.message_crud.count_messages(chat_id)
        return count

def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db)
