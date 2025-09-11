from fastapi import FastAPI
from app.database.config import check_db_connection
from app.rag.ollama import check_ollama_connection
from app.routers.rag import router as rag_router
from app.routers.ollama import router as ollama_router
from app.setting.config import get_settings

app = FastAPI()

app.include_router(rag_router, prefix="/api")
app.include_router(ollama_router, prefix="/api")


# API Test Status System
@app.get("/api/health")
async def health():
    db_connect = await check_db_connection()
    ollama_connect = await check_ollama_connection()
    get_settings.cache_clear()
    return {
        "db_connection": db_connect,
        "ollama_connection": ollama_connect,
        "server_status": "Running",
        "configs": get_settings()
    }