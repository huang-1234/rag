from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

class VectorService:
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        """
        初始化向量服务

        Args:
            model_name: 向量模型名称
        """
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(self.host, port=self.port)
        self.encoder = SentenceTransformer(model_name)
        self.vector_size = self.encoder.get_sentence_embedding_dimension()

    def create_collection(self, collection_name: str = "docs"):
        """
        创建向量集合

        Args:
            collection_name: 集合名称
        """
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE
            )
        )

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return self.encoder.encode(texts).tolist()

    async def encode_async(self, texts: List[str]) -> List[List[float]]:
        """
        异步将文本编码为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode, texts)

    async def upsert(self, vectors: List[List[float]], payloads: List[Dict[str, Any]],
                    collection_name: str = "docs", ids: Optional[List[str]] = None) -> bool:
        """
        添加或更新向量

        Args:
            vectors: 向量列表
            payloads: 元数据列表
            collection_name: 集合名称
            ids: 可选的ID列表

        Returns:
            是否成功
        """
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=models.Batch(
                    vectors=vectors,
                    payloads=payloads,
                    ids=ids or list(range(len(vectors)))
                )
            )
            return True
        except Exception as e:
            print(f"向量插入错误: {e}")
            return False

    async def search(self, query: str, top_k: int = 5,
                    collection_name: str = "docs") -> List[Dict[str, Any]]:
        """
        向量搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            collection_name: 集合名称

        Returns:
            搜索结果列表
        """
        vector = await self.encode_async([query])
        results = self.client.search(
            collection_name=collection_name,
            query_vector=vector[0],
            limit=top_k,
            with_payload=True
        )

        return results

@lru_cache(maxsize=1)
def get_vector_service(model_name: str = "BAAI/bge-large-zh-v1.5") -> VectorService:
    """
    获取向量服务单例

    Args:
        model_name: 向量模型名称

    Returns:
        向量服务实例
    """
    return VectorService(model_name=model_name)