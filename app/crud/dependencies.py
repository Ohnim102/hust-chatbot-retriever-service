from typing import AsyncGenerator
from app.crud.chat import ChatCRUD
from app.database.config import async_session


async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        async with session.begin():
            yield session

async def get_chat_crud() -> AsyncGenerator:
    async with async_session() as session:
        async with session.begin():
            yield ChatCRUD(session)
