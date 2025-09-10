import os
from functools import lru_cache
from dotenv import load_dotenv
# from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()
# model_config = SettingsConfigDict(env_file=".env")
class Settings():
    app_name: str = "Retriever Service"
    author: str = "MinhDN"
    version: str = "1.0.0"
    database_url: str = "postgresql+asyncpg://postgres:1234567890@localhost:5432/postgres"
    ollama_url: str = "http://localhost:11434"
    # ollama_url: str = "http://ollama:11434"
    ollama_timeout: int = 600
    chromadb_persist_directory: str = "chroma_db"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()