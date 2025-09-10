
from typing import List

from fastapi import Depends
from app.crud.chat import ChatCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.dependencies import get_chat_crud, get_db
from app.schemas.chat import Message, MessageCreate
from app.schemas.chat import Chat

from typing import Optional
from datetime import datetime
from app.models.chat import MessageModels
from sqlalchemy import select


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_crud = ChatCRUD(self.db)
    
    async def get(self, page: int = 1, size: int = 10) -> List[Chat]:
        chats = await self.chat_crud.get_chats(page=page, size=size)
        return chats

    async def insert(self, input: Chat) -> Chat:
        new_chat = await self.chat_crud.create_chat(input)


        return new_chat.get('ChatModels', {})

    async def update(self, input: Chat) -> Chat:
        updated_chat = await self.chat_crud.update_chat(input)
        return updated_chat

    async def delete(self, input_id: int) -> None:
        await self.chat_crud.delete_chat(input_id)

    async def retrieval_by_input(self, input: str) -> List[Chat]:
        chats = await self.chat_crud.get_chats_by_input(input)
        return chats
    async def get_by_id(self, chat_id: int) -> Optional[Chat]:
        chat_model = await self.chat_crud.get_chat_by_id(chat_id)
        if chat_model:
            return Chat.from_orm(chat_model)
            # if chat_model.messages is None:
            #     chat_model.messages = []  # Gán mảng rỗng nếu không có messages
            # return Chat.from_orm(chat_model)
        return None
    
    async def get_by_id_public(self, chat_id: int) -> Optional[Chat]:
        chat_model = await self.chat_crud.get_chat_by_id(chat_id)
        if chat_model:
            return Chat.from_orm(chat_model)
        return None

    
    async def add_message(self, chat_id: int, message_create: MessageCreate) -> Optional[Message]:
        chat = await self.get_by_id_public(chat_id)
        if not chat:
            return None
        new_message_model = MessageModels(
            chat_id=chat_id,
            role=message_create.role,
            content=message_create.content,
            tokens=message_create.tokens,
            model=message_create.model
        )
        self.db.add(new_message_model)
        await self.db.flush()
    
        return Message.from_orm(new_message_model)


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)