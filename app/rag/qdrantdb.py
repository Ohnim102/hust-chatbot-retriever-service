import os
import getpass
from typing import List
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.schemas.document import Document
from app.setting.config import get_settings
from uuid import uuid4
from app.setting.enum import DocsCollection


class QdrantDB:
    def __init__(
        self,
        collection_name: DocsCollection = DocsCollection.SEARCH,
        url: str = get_settings().qdrant_url,
        api_key: str = None,
        embedding_size: int = 768,  # nomic-embed-text dimension
        distance: Distance = Distance.COSINE,
        in_memory: bool = False,
    ):
        self.database = "hust"
        self.collection_name = str(collection_name.value) if hasattr(collection_name, 'value') else str(collection_name)
        self.url = url
        self.api_key = api_key
        self.embedding_size = embedding_size
        self.distance = distance
        
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=get_settings().ollama_url,
            client_kwargs={"timeout": 600},
        )

        # Khởi tạo Qdrant client
        if in_memory:
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
            )
        
        # Tạo collection nếu chưa tồn tại
        self._create_collection_if_not_exists()
        
        # Khởi tạo vector store
        self.qdrantdb = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=embeddings,
        )

    def _create_collection_if_not_exists(self):
        """Tạo collection nếu chưa tồn tại"""
        try:
            # Kiểm tra xem collection đã tồn tại chưa
            collections = self.client.get_collections().collections
            collection_exists = any(col.name == self.collection_name for col in collections)
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size, 
                        distance=self.distance
                    ),
                )
        except Exception as e:
            print(f"Error creating collection: {e}")

    async def add_documents(self, documents, metadatas=None):
        uuids = [str(uuid4()) for _ in range(len(documents))]
        await self.qdrantdb.aadd_documents(documents=documents, ids=uuids)

    # Query QdrantDB
    def query(self, query: str, top_k: int):
        results = self.qdrantdb.similarity_search_with_relevance_scores(
            query=query, k=top_k
        )
        return results

    # Additional search methods
    def similarity_search(self, query: str, top_k: int):
        """Tìm kiếm documents tương tự (chỉ trả về documents)"""
        return self.qdrantdb.similarity_search(
            query=query, k=top_k
        )

    def similarity_search_by_vector(self, embedding: List[float], top_k: int):
        """Tìm kiếm bằng vector embedding"""
        return self.qdrantdb.similarity_search_by_vector(
            embedding=embedding, k=top_k
        )

    def max_marginal_relevance_search(self, query: str, top_k: int = 5, fetch_k: int = 20, lambda_mult: float = 0.5):
        """Tìm kiếm với Max Marginal Relevance để tránh duplicate"""
        return self.qdrantdb.max_marginal_relevance_search(
            query=query,
            k=top_k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult
        )

    # Dangerous Function - Clear all data in collection
    def clear_qdrant_collection(self):
        try:
            # Xóa collection
            self.client.delete_collection(collection_name=self.collection_name)
            
            # Tạo lại collection
            self._create_collection_if_not_exists()
            
            # Khởi tạo lại vector store
            embeddings = OllamaEmbeddings(
                model="nomic-embed-text",
                base_url=get_settings().ollama_url,
                client_kwargs={"timeout": 600},
            )
            
            self.qdrantdb = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=embeddings,
            )
            
            return True
        except Exception as e:
            print(f"Error clearing Qdrant collection: {e}")
            return False

    def delete_collection(self):
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            return True
        except Exception as e:
            print(f"Error deleting Qdrant collection: {e}")
            return False

    def delete_documents(self, ids: List[str]):
        """Xóa documents theo IDs"""
        try:
            self.qdrantdb.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    def get_collection_info(self):
        """Lấy thông tin về collection"""
        try:
            return self.client.get_collection(collection_name=self.collection_name)
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None

    def get_collection_stats(self):
        """Lấy thống kê collection"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return info.points_count if info else 0
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return 0

    def add_texts(self, texts: List[str], metadatas: List[dict] = None):
        """Thêm texts vào collection (đồng bộ)"""
        uuids = [str(uuid4()) for _ in range(len(texts))]
        return self.qdrantdb.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=uuids
        )

    def search_by_filter(self, query: str, filter_dict: dict, top_k: int = 5):
        """Tìm kiếm với filter"""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            
            # Tạo filter từ dict (đơn giản hóa, có thể mở rộng)
            filter_conditions = []
            for key, value in filter_dict.items():
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            
            qdrant_filter = Filter(must=filter_conditions)
            
            return self.qdrantdb.similarity_search(
                query=query,
                k=top_k,
                filter=qdrant_filter
            )
        except Exception as e:
            print(f"Error searching with filter: {e}")
            return []

    def update_collection_config(self, embedding_size: int = None, distance: Distance = None):
        """Cập nhật cấu hình collection (cần xóa và tạo lại)"""
        try:
            if embedding_size:
                self.embedding_size = embedding_size
            if distance:
                self.distance = distance
                
            # Xóa và tạo lại collection với config mới
            return self.clear_qdrant_collection()
        except Exception as e:
            print(f"Error updating collection config: {e}")
            return False

    def close_connection(self):
        """Đóng kết nối"""
        try:
            self.client.close()
        except Exception as e:
            print(f"Error closing connection: {e}")