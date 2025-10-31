import os
import json
from functools import lru_cache
from dotenv import load_dotenv
# from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()

SETTINGS_FILE = os.getenv("APP_SETTINGS_FILE", os.path.join(os.getcwd(), "appsettings.json"))
_DEFAULTS = {
    # "app_name": "Retriever Service",
    # "author": "MinhDN",
    # "version": "1.0.0",
    # "database_url": "",
    # "ollama_url": "http://localhost:11434",
    # "qdrant_url": "http://localhost:6333",
    # "ollama_timeout": 600,
    # "chromadb_persist_directory": "chroma_db"
}

def _load_json_settings(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

class Settings:
    def __init__(self, data: dict):
        # Merge: defaults <- file <- environment variables
        merged = {**_DEFAULTS, **(data or {})}

        # Gọi environment overrides (nếu có)
        merged["app_name"] = os.getenv("APP_NAME", merged.get("app_name"))
        merged["author"] = os.getenv("AUTHOR", merged.get("author"))
        merged["version"] = os.getenv("VERSION", merged.get("version"))
        merged["database_url"] = os.getenv("DATABASE_URL", merged.get("database_url"))
        merged["ollama_url"] = os.getenv("OLLAMA_URL", merged.get("ollama_url"))
        merged["qdrant_url"] = os.getenv("QDRANT_URL", merged.get("qdrant_url"))
        merged["ollama_timeout"] = int(os.getenv("OLLAMA_TIMEOUT", merged.get("ollama_timeout")))
        merged["chromadb_persist_directory"] = os.getenv("CHROMADB_PERSIST_DIRECTORY", merged.get("chromadb_persist_directory"))

        self.app_name: str = merged["app_name"]
        self.author: str = merged["author"]
        self.version: str = merged["version"]
        self.database_url: str = merged["database_url"]
        self.ollama_url: str = merged["ollama_url"]
        self.qdrant_url: str = merged["qdrant_url"]
        self.ollama_timeout: int = merged["ollama_timeout"]
        self.chromadb_persist_directory: str = merged["chromadb_persist_directory"]

@lru_cache()
def get_settings():
    data = _load_json_settings(SETTINGS_FILE)
    return Settings(data)

settings = get_settings()
print(f"Settings loaded: {settings.__dict__}")