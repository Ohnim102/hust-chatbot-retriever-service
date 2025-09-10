import httpx
from app.setting.config import get_settings

async def check_ollama_connection() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(get_settings().ollama_url)
            if response.status_code == 200:
                return True
            else:
                return False
    except httpx.RequestError as e:
        print(f"Lỗi kết nối tới Ollama: {e}")
        return False