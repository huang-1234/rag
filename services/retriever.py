from typing import List, Dict, Any, Optional, Tuple
import asyncio
import time
import numpy as np
from rank_bm25 import BM25Okapi
from elasticsearch import AsyncElasticsearch
import redis.asyncio as aioredis
import json
import os

from .vector import VectorService, get_vector_service

class HybridRetriever:
    """混合检索服务，结合向量检索和关键词检索"""

    def __init__(self, vector_service: Optional[VectorService] = None):
        """
        初始化混合检索服务

        Args:
            vector_service: 向量服务实例
        """
        self.vector = vector_service or get_vector_service()

        # 初始化Elasticsearch客户端
        self.es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.es_port = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
        self.es = AsyncElasticsearch(f"http://{self.es_host}:{self.es_port}")
        self.index_name = "docs"

        # 初始化Redis客户端
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = aioredis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)

        # BM25初始化标志
        self.bm25_initialized = False
        self.documents = []
        self.bm25 = None

    async def initialize(self):
        """初始化检索器，加载必要的数据"""
        # 尝试从Elasticsearch加载文档
        try:
            await self._init_bm25()
        except Exception as e:
            print(f"BM25初始化错误: {e}")

    async def _init_bm25(self):
        """从Elasticsearch加载文档初始化BM25"""
        try:
            # 检查索引是否存在
            if not await self.es.indices.exists(index=self.index_name):
                print(f"索引 {self.index_name} 不存在，跳过BM25初始化")
                return

            # 从ES获取文档
            result = await self.es.search(
                index=self.index_name,
                body={"query": {"match_all": {}}, "size": 1000}
            )

            if result["hits"]["total"]["value"] == 0:
                print("没有找到文档，跳过BM25初始化")
                return

            # 提取文档内容
            self.documents = []
            texts = []

            for hit in result["hits"]["hits"]:
                doc = hit["_source"]
                doc_id = hit["_id"]
                content = doc.get("content", "")

                if content:
                    self.documents.append({
                        "id": doc_id,
                        "content": content,
                        "metadata": {k: v for k, v in doc.items() if k != "content"}
                    })
                    texts.append(content)

            # 初始化BM25
            tokenized_texts = [doc.split() for doc in texts]
            self.bm25 = BM25Okapi(tokenized_texts)
            self.bm25_initialized = True

            print(f"BM25初始化完成，加载了 {len(self.documents)} 个文档")
        except Exception as e:
            print(f"BM25初始化错误: {e}")
            self.bm25_initialized = False

    async def retrieve(self, query: str, top_k: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_cache: 是否使用缓存

        Returns:
            检索结果列表
        """
        start_time = time.time()

        # 检查缓存
        if use_cache:
            cache_key = f"search:{query}:{top_k}"
            cached_result = await self.redis.get(cache_key)
            if cached_result:
                try:
                    return json.loads(cached_result)
                except:
                    pass

        # 并行执行向量检索和关键词检索
        vector_future = self._vector_search(query, top_k * 2)
        keyword_future = self._keyword_search(query, top_k * 2)

        vector_results, keyword_results = await asyncio.gather(vector_future, keyword_future)

        # 融合结果
        combined_results = self._fuse_results(query, vector_results, keyword_results)
        final_results = combined_results[:top_k]

        # 添加元数据
        for result in final_results:
            result["latency"] = time.time() - start_time
            result["search_method"] = "hybrid"

        # 缓存结果
        if use_cache:
            cache_key = f"search:{query}:{top_k}"
            await self.redis.setex(cache_key, 3600, json.dumps(final_results))

        return final_results

    async def _vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        try:
            results = await self.vector.search(query, top_k=top_k)
            return [
                {
                    "id": str(result.id),
                    "score": float(result.score),
                    "content": result.payload.get("content", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k != "content"},
                    "source": "vector"
                }
                for result in results
            ]
        except Exception as e:
            print(f"向量检索错误: {e}")
            return []

    async def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        关键词检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        # 尝试使用Elasticsearch
        try:
            if await self.es.indices.exists(index=self.index_name):
                result = await self.es.search(
                    index=self.index_name,
                    body={
                        "query": {
                            "multi_match": {
                                "query": query,
                                "fields": ["content^3", "title^2", "metadata.*"],
                                "fuzziness": "AUTO"
                            }
                        },
                        "size": top_k
                    }
                )

                return [
                    {
                        "id": hit["_id"],
                        "score": hit["_score"],
                        "content": hit["_source"].get("content", ""),
                        "metadata": {k: v for k, v in hit["_source"].items() if k != "content"},
                        "source": "elasticsearch"
                    }
                    for hit in result["hits"]["hits"]
                ]
        except Exception as e:
            print(f"Elasticsearch检索错误: {e}")

        # 回退到BM25
        try:
            if self.bm25_initialized and self.bm25:
                tokenized_query = query.split()
                doc_scores = self.bm25.get_scores(tokenized_query)
                top_indices = np.argsort(doc_scores)[::-1][:top_k]

                return [
                    {
                        "id": self.documents[i]["id"],
                        "score": float(doc_scores[i]),
                        "content": self.documents[i]["content"],
                        "metadata": self.documents[i]["metadata"],
                        "source": "bm25"
                    }
                    for i in top_indices if i < len(self.documents)
                ]
        except Exception as e:
            print(f"BM25检索错误: {e}")

        return []

    def _fuse_results(self, query: str, vector_results: List[Dict[str, Any]],
                     keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        融合向量检索和关键词检索结果

        Args:
            query: 查询文本
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果

        Returns:
            融合后的结果列表
        """
        # 使用RRF(Reciprocal Rank Fusion)算法
        fused_scores = {}

        # 处理向量检索结果
        for i, result in enumerate(vector_results):
            doc_id = result["id"]
            # RRF公式: 1 / (k + rank)，其中k是常数，通常取60
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (60.0 + i)

        # 处理关键词检索结果
        for i, result in enumerate(keyword_results):
            doc_id = result["id"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (60.0 + i)

        # 合并结果
        merged_results = {}
        for result in vector_results + keyword_results:
            doc_id = result["id"]
            if doc_id not in merged_results:
                merged_results[doc_id] = result

        # 添加融合分数
        final_results = []
        for doc_id, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True):
            if doc_id in merged_results:
                result = merged_results[doc_id].copy()
                result["score"] = score
                final_results.append(result)

        return final_results