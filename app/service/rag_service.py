from typing import List, Dict
import os
from fastapi import Depends, UploadFile
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredExcelLoader,
)
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from app.models.document import Document
# from app.rag.chromadb import ChromaDB
from app.rag.qdrantdb import QdrantDB
import re
import unicodedata
from app.transformers.rag_file_transformer import transform_documents
from app.transformers.rag_content_transformer import transform_to_content
from app.setting.enum import DocsCollection
from app.models.prompt import OllamaPrompt, OllamaMessage


class RAGService:
    def __init__(self):
        self.chatid = 1;

    def clean_text(self, text: str) -> str:
        return text.strip()

    def is_meaningful(self, text: str) -> bool:
        if re.search(r"(g cÇ|H£¯|Dxcl|TlÑ¡|pệ|ÝÎ|¯lầ|ĐầÇ|g l|gI|Áx|Á²|Áà|Ì)", text):
            return False
        count_alpha = sum(c.isalpha() for c in text)
        count_visible = sum(1 for c in text if c.isprintable())
        if count_visible == 0 or (count_alpha / count_visible) < 0.5:
            return False
        count_weird = sum(
            1 for c in text if not re.match(r"[a-zA-ZÀ-ỹà-ỹ0-9\s.,!?\"'’\-–()]", c)
        )
        if count_weird / len(text) > 0.2:
            return False
        count_control = sum(1 for c in text if unicodedata.category(c).startswith("C"))
        if count_control > 0:
            return False
        if re.fullmatch(r"^[\W\d\s]+$", text.strip()):
            return False

        return True

    # Clean documents before embedding
    async def clean_documents(self, documents: List[Document]) -> List[Document]:
        cleaned_docs = []
        for doc in documents:
            text = doc.page_content
            # Except for the first document which is the file name
            if not text.startswith("Tên file"):
                # 1.Clean page_content
                text = text.replace("\r\n", " ").replace("\n", " ").replace("\t", " ")
                text = re.sub(r"[^\x20-\x7EÀ-ỹ\u00A0-\uFFFF]", "", text)
                text = re.sub(r"\s+", " ", text)
                text = re.sub(r"[.,!?;:]+", ".", text)
                text = re.sub(r"^[.,!?;:]+", "", text)
                text = re.sub(r"[.,!?;:]+$", ".", text)
                text = text.strip()

                if len(text.strip().split()) < 6:
                    continue
                if re.fullmatch(r"[\W\d\s]+", text):
                    continue
                # if not self.is_meaningful(text):
                #     continue
            doc.page_content = text
            print(f"Content doc after cleaning: {text}")

            # 2.Clean metadata
            if doc.metadata is not None:
                metadata_fields_to_remove = [
                    "moddate",
                    "creator",
                    "producer",
                    "page_label",
                ]
                for field in metadata_fields_to_remove:
                    if field in doc.metadata:
                        del doc.metadata[field]

            cleaned_docs.append(doc)

        return cleaned_docs

    def add_file_name_to_start(
        self, metadata, documents: List[Document]
    ) -> List[Document]:
        source_path = metadata.get("source", "")
        file_name = os.path.basename(source_path)
        if not file_name:
            file_name = "Untitled"

        file_doc = Document(page_content="Tên file: " + file_name, metadata=metadata)
        documents.insert(0, file_doc)

        return documents

    # Load and split document
    async def load_and_split_document(
        self,
        doc_id: str,
        file_path: str,
        collection_name: DocsCollection,
        options: Dict[str, any] = {
            "chunk_size": 120,
            "chunk_overlap": 0,
        },
    ) -> str:
        # TODO: Handle file pdf with UnstructuredPDFLoader
        documents = None
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(file_path)
        elif file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

        documents = loader.load()
        metadata = documents[0].metadata
        for doc in documents:
            doc.page_content = self.clean_text(doc.page_content)

        # Split documents into smaller chunks
        if documents:
            documents = self.split_documents(documents, options)

        documents_add_page_name = self.add_file_name_to_start(metadata, documents)
        documents_cleaned = await self.clean_documents(documents_add_page_name)
        await self.add_to_vector_db(doc_id, documents_cleaned, collection_name)

        return file_path

    # Query document from VectorDB
    async def query_document(
        self, collection_name: DocsCollection, query: str, k: int = 5
    ):
        vectordb_instance = QdrantDB(collection_name=collection_name)
        documents = vectordb_instance.query(query, k)

        return transform_documents(documents)

    async def query_rag_content_document(
        self, collection_name: DocsCollection, query: str, k: int = 5
    ):
        vectordb_instance = QdrantDB(collection_name=collection_name)
        documents = vectordb_instance.query(query, k)

        return transform_to_content(documents)

    async def add_to_vector_db(
        self, doc_id: str, documents: List[Document], collection_name: DocsCollection
    ) -> List[Document]:
        vectordb_instance = QdrantDB(collection_name=collection_name)
        await vectordb_instance.add_documents(doc_id, documents)

        return True

    async def delete_documents_by_doc_id(
            self, doc_id: str, collection_name: DocsCollection
    ):
        vectordb_instance = QdrantDB(collection_name=collection_name)
        vectordb_instance.delete_documents_by_doc_id(doc_id)

        return True
        

    async def clear_vectordb(self, collection_name: DocsCollection) -> bool:
        vectordb_instance = QdrantDB(collection_name=collection_name)
        return vectordb_instance.delete_collection()

    def split_documents(
        self,
        documents: List[Document],
        options: Dict[str, any] = {
            "chunk_size": 120,
            "chunk_overlap": 0,
        },
    ) -> List[Document]:
        # Split document by priority level
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=options.get("chunk_size", 120),
            chunk_overlap=options.get("chunk_overlap", 0),
            separators=["\n\n", "\n", ". ", "! ", "? ", "+ ", "- ", " ", ""],
        )

        texts = text_splitter.split_documents(documents)
        return texts

    async def generate_prompt(self, 
                              query: str, 
                              collection: DocsCollection = DocsCollection.SEARCH
                              ) -> List[Dict[str, str]]:
        """
        Generate a prompt for the RAG model using the query and context documents.

        Args:
            query (str): The user's query.

        Returns:
            OllamaPrompt: The generated prompt.
        """
        # Lấy ngữ cảnh từ cơ sở dữ liệu Vector DB
        context_documents = await self.query_document(
            collection, query, k=5
        )

        # Nếu không có tài liệu ngữ cảnh, trả về thông báo không có thông tin
        if not context_documents:
            context_documents = "Không có thông tin nào để trả lời câu hỏi này."

        prompt_messages = [
            dict(
                role="user",
                content=f"""Bạn là một trợ lý AI có tên là a.Guide thuộc trường Đại học Bách Khoa Hà Nội. 
                Nhiệm vụ của bạn là trả lời câu hỏi bằng tiếng việt dựa trên các tài liệu đã được cung cấp. 
                Hãy trả lời câu hỏi một cách ngắn gọn, súc tích và rõ ràng, trích ra nguồn của tài liệu nếu có thể. 
                Nếu câu hỏi không liên quan đến tài liệu, bạn có thể dùng kiến thức của mình để trả lời câu hỏi.
                Nếu câu hỏi không rõ ràng hoặc không đầy đủ, hãy yêu cầu người dùng cung cấp thêm thông tin. 
                Câu hỏi như sau: \n{query}""",
            ),
            dict(role="user", content=f"Tài liệu:\n{context_documents}"),
        ]

        return prompt_messages


def get_rag_service() -> RAGService:
    return RAGService()
