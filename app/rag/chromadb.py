import os
import shutil
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.setting.config import get_settings
from app.setting.enum import DocsCollection

class ChromaDB:
    def __init__(
        self,
        collection_name: DocsCollection = DocsCollection.SEARCH,
    ):
        self.database = "hust"
        self.collection_name = collection_name
        self.persist_directory = f"./chromadb"
        os.makedirs(self.persist_directory, exist_ok=True)

        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=get_settings().ollama_url,
            client_kwargs={"timeout": 600},
        )

        self.chromadb = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings,
            persist_directory=self.persist_directory,
        )

    async def add_documents(self, documents, metadatas=None):
        uuids = [str(uuid4()) for _ in range(len(documents))]
        await self.chromadb.aadd_documents(documents=documents, ids=uuids)

    # Query ChromaDB
    def query(self, query: str, top_k: int):
        results = self.chromadb.similarity_search_with_relevance_scores(
            query=query, k=top_k
        )
        return results

    # Dangerous Function
    def clear_chroma_folder(self):
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        import stat

        os.chmod(self.persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        return True

    def delete_collection(self):
        self.chromadb.delete_collection()
        return True
