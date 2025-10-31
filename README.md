# Retriever service


## 📋 Overview

API này cung cấp các chức năng cho hệ thống Retrieval-Augmented Generation (RAG), bao gồm:
- Upload tài liệu vào VectorDB
- Truy vấn tài liệu
- Sinh prompt cho LLM
- Xóa tài liệu theo doc_id
- Xoá tài liệu hoặc toàn bộ VectorDB

Retriever service:
- Base URL: `http://localhost:8081/api/`  
- Swagger: `http://localhost:8081/docs`

Qdrant DB: `http://localhost:6333/dashboard#/collections`  
Chroma DB: `http://127.0.0.1:8000/docs/`

## 🚀 Deploy

```sh
# build image
docker build -t retriever-service .

# run
docker compose up -d

# pull ollama model
docker exec ollama ollama pull nomic-embed-text

# docker exec ollama ollama pull deepseek-r1:8b
```

### Cấu trúc project:
```
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
```

## Installation
Cài đặt thư viện
```python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt 
```

Run Ollama và Qdrant
```sh
docker compose run ollama
docker compose run qdrant
```

ssh vào container Ollama
```sh
ollama pull nomic-embed-text
ollama pull deepseek-r1:8b  # Option
```


## 🧩 API Endpoints

### 1. Upload Document for RAG

Upload tài liệu để đưa vào hệ thống RAG.

**Endpoint**: `POST /api/rag/upload-for-rag`

**Tags**: `rag`

**Request Body** (multipart/form-data):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `doc_id` | string | ✅ | - | ID định danh cho tài liệu |
| `file` | binary | ✅ | - | File tài liệu cần upload |
| `collection` | string | ❌ | `rag_collection` | Tên collection để lưu trữ (`rag_collection` hoặc `search_collection`) |

**Response**:
- `200`: Upload thành công
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X POST "http://api.example.com/api/rag/upload-for-rag" \
  -F "doc_id=doc123" \
  -F "file=@document.pdf" \
  -F "collection=rag_collection"
```

**Example Response**:
  `"./temp_uploads\\Hà Nội.pdf"`

---

### 2. Delete Document by ID

Xóa tài liệu khỏi vector database theo doc_id.

**Endpoint**: `DELETE /api/rag/delete-document-by-doc-id`

**Tags**: `rag`

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doc_id` | string | ✅ | - | ID của tài liệu cần xóa |
| `collection` | string | ❌ | `rag_collection` | Tên collection chứa tài liệu |

**Response**:
- `200`: Xóa thành công
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X DELETE "http://api.example.com/api/rag/delete-document-by-doc-id?doc_id=doc123&collection=rag_collection"
```

**Example Response**:
```json
{
  "success": true,
  "doc_id": "987654321"
}
```
---

### 3. Query Document

Tìm kiếm tài liệu trong vector database.

**Endpoint**: `GET /api/rag/query`

**Tags**: `rag`

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Câu truy vấn tìm kiếm |
| `k` | integer | ✅ | - | Số lượng kết quả trả về |
| `collection` | string | ❌ | `rag_collection` | Tên collection để tìm kiếm |

**Response**:
- `200`: Trả về kết quả tìm kiếm
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X GET "http://api.example.com/api/rag/query?query=machine%20learning&k=5&collection=rag_collection"
```

**Example Response**:
```json
[
    {
        "source": "./temp_uploads\\Vincom Landmark 81.docx",
        "metadata": {
            "source": "./temp_uploads\\Vincom Landmark 81.docx",
            "total_pages": 0,
            "creationdate": "",
            "title": "Untitled",
            "author": "Unknown Author"
        },
        "matches": [
            {
                "page_content": "Riêng tầng 21. 46H và 78 là tầng kĩ thuật.",
                "score": 0.75985098,
                "page": 0
            },
            {
                "page_content": "Tên file: Vincom Landmark 81.docx",
                "score": 0.674089315,
                "page": 0
            }
        ]
    }
]
```

---

### 4. Generate Prompt

Tạo prompt dựa trên câu truy vấn và context từ vector database.

**Endpoint**: `GET /api/rag/generate-prompt`

**Tags**: `rag`

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Câu truy vấn |
| `collection` | string | ❌ | `rag_collection` | Tên collection để lấy context |

**Response**:
- `200`: Trả về prompt đã được tạo
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X GET "http://api.example.com/api/rag/generate-prompt?query=what%20is%20AI&collection=rag_collection"
```

---

### 5. Clear Vector Database

Xóa toàn bộ dữ liệu trong một collection.

**Endpoint**: `GET /api/rag/clear-vectordb`

**Tags**: `rag`

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `collection` | string | ✅ | - | Tên collection cần xóa (`rag_collection` hoặc `search_collection`) |

**Response**:
- `200`: Xóa thành công
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X GET "http://api.example.com/api/rag/clear-vectordb?collection=rag_collection"
```

---

## Ollama Endpoints

### 6. Chat Stream

Gửi request chat đến Ollama với khả năng streaming response.

**Endpoint**: `POST /api/ollama/chat/stream`

**Tags**: `ollama`

**Request Body** (application/json):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | ✅ | - | Tên model Ollama sử dụng |
| `messages` | array | ✅ | - | Danh sách các message trong cuộc hội thoại |
| `chat_id` | integer/null | ❌ | `null` | ID của chat session |
| `options` | object/null | ❌ | `null` | Các tùy chọn bổ sung cho model |
| `streaming` | boolean/null | ❌ | `true` | Bật/tắt streaming response |

**Request Body Example**:
```json
{
  "model": "llama2",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is machine learning?"
    }
  ],
  "chat_id": 123,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9
  },
  "streaming": true
}
```

**Response**:
- `200`: Trả về response từ Ollama (streaming hoặc non-streaming)
- `422`: Lỗi validation

**Example cURL**:
```bash
curl -X POST "http://api.example.com/api/ollama/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "streaming": true
  }'
```

---

### 7. Get Models

Lấy danh sách các model Ollama có sẵn.

**Endpoint**: `GET /api/ollama/models`

**Tags**: `ollama`

**Response**:
- `200`: Trả về danh sách models

**Example cURL**:
```bash
curl -X GET "http://api.example.com/api/ollama/models"
```

---

## Health Check

### 8. Health Check

Kiểm tra trạng thái hoạt động của API.

**Endpoint**: `GET /api/health`

**Response**:
- `200`: API đang hoạt động bình thường

**Example cURL**:
```bash
curl -X GET "http://api.example.com/api/health"
```


## Tham khảo
- [Tesseract ](https://github.com/UB-Mannheim/tesseract/wiki)
- [ChatGPT](https://chatgpt.com/c/69037dcc-49b0-8324-884c-23cfc09c95b6)