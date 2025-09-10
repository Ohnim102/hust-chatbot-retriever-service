Khởi tạo project
python -m venv .venv
.venv\Scripts\activate

Tạo file requirements.txt (dưới) hoặc dùng pip install trực tiếp:
- pip install chromadb sentence-transformers fastapi uvicorn python-multipart
Hoặc:
- Install requirements: pip install -r requirements.txt 


Cấu trúc project:
retriever-chromadb/
├─ .venv/
├─ .vscode/
│  ├─ launch.json
│  └─ settings.json
├─ requirements.txt
├─ retriever_service.py
├─ ingest.py
├─ utils.py
├─ Dockerfile
└─ docker-compose.yml
