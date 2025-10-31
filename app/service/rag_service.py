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
# from pdf2image import convert_from_path

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from pdfminer.high_level import extract_text

# from docling.parsers import PdfParser, WordParser, HtmlParser, ExcelParser
# from docling.document_converter import DocumentConverter

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
import platform


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
    
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    else:
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

    @staticmethod
    def pdf_to_text_ocr_fitz(file_path: str, lang: str = "vie") -> str:
        """
        Đọc file PDF scan (image-based) bằng PyMuPDF và Tesseract OCR.
        Không cần Poppler.
        """
        text_result = ""
        doc = fitz.open(file_path)
        print(f"🔍 Found {doc.page_count} pages in {file_path}")

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=300)  # render với độ phân giải cao
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

            # OCR
            text = pytesseract.image_to_string(img, lang=lang)
            text_result += f"\n=== Page {page_index + 1} ===\n{text}\n"

        return text_result
    
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
        ext = os.path.splitext(file_path)[1].lower()
        documents: List[Document] = []

        ## --- Using Langchain loaders ---
        # if file_path.endswith(".pdf"):
        #     loader = PyPDFLoader(file_path)
        # elif file_path.endswith(".docx"):
        #     loader = Docx2txtLoader(file_path)
        # elif file_path.endswith(".xlsx"):
        #     loader = UnstructuredExcelLoader(file_path)
        # elif file_path.endswith(".html"):
        #     loader = UnstructuredHTMLLoader(file_path)
        # else:
        #     raise ValueError(f"Unsupported file type: {file_path}")
        # documents = loader.load()

        ## --- Using Docling library (not maintained) ---
        # converter = DocumentConverter()
        # result = converter.convert(file_path)
        # text = result.document.export_to_text()
        # documents = [Document(page_content=text, metadata={"source": file_path})]

        ## --- Using UnstructuredPDFLoader with OCR fallback ---
        if ext == ".pdf":
            try:
                text = extract_text(file_path)
                if text and len(text.strip()) > 20:
                    print("📄 PDF has text layer — using PyPDFLoader")
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                else:
                    full_text = RAGService.pdf_to_text_ocr_fitz(file_path, lang="vie")
                    full_text = self.pdf_to_text_ocr_fitz(file_path, lang="vie")
                    documents = [Document(page_content=full_text, metadata={"source": file_path})]
            except Exception as e:
                print(f"⚠️ OCR fallback failed: {e}")
                raise ValueError(f"OCR fallback failed: {file_path}")
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
        elif ext in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
            documents = loader.load()
        elif ext in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(file_path)
            documents = loader.load()
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                documents = [Document(page_content=text, metadata={"source": file_path})]
        else:
            raise ValueError(f"Unsupported file type: {file_path}")        

        for doc in documents:
            doc.page_content = self.clean_text(doc.page_content)

        # Split documents into smaller chunks
        if documents:
            documents = self.split_documents(documents, options)

        documents_add_page_name = self.add_file_name_to_start(documents[0].metadata, documents)
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
