from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
import time
from typing import List, Dict, Any, Optional

from services.retriever import HybridRetriever
from models.document import RAGRequest, RAGResponse

router = APIRouter(prefix="/v1/rag", tags=["RAG Service"])

async def get_retriever() -> HybridRetriever:
    """获取检索器实例"""
    retriever = HybridRetriever()
    await retriever.initialize()
    return retriever

@router.post(
    "/query",
    summary="RAG核心查询接口",
    response_model=RAGResponse,
    responses={
        200: {"description": "成功返回相关文档"},
        400: {"description": "无效请求参数"},
        500: {"description": "服务器内部错误"}
    }
)
async def rag_query(
    request: RAGRequest = Body(...),
    retriever: HybridRetriever = Depends(get_retriever)
) -> RAGResponse:
    """
    支持混合检索的RAG接口，返回top_k相关文档

    - **query**: 查询文本
    - **top_k**: 返回结果数量
    - **temperature**: 温度参数（用于后续LLM生成）
    - **use_cache**: 是否使用缓存
    - **filters**: 可选的过滤条件
    """
    try:
        start_time = time.time()

        # 应用过滤器
        filters = request.filters or {}

        # 执行检索
        results = await retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            use_cache=request.use_cache
        )

        return RAGResponse(
            results=results,
            latency=time.time() - start_time,
            search_method="hybrid"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

@router.get(
    "/health",
    summary="RAG服务健康检查",
    responses={
        200: {"description": "服务正常"},
        500: {"description": "服务异常"}
    }
)
async def health_check():
    """
    检查RAG服务的健康状态
    """
    try:
        # 创建检索器实例
        retriever = HybridRetriever()

        # 检查向量服务
        vector_status = "ok"
        try:
            # 简单查询测试
            await retriever.vector.search("test", top_k=1)
        except Exception as e:
            vector_status = f"error: {str(e)}"

        # 检查Elasticsearch
        es_status = "ok"
        try:
            await retriever.es.info()
        except Exception as e:
            es_status = f"error: {str(e)}"

        # 检查Redis
        redis_status = "ok"
        try:
            await retriever.redis.ping()
        except Exception as e:
            redis_status = f"error: {str(e)}"

        return {
            "status": "healthy",
            "services": {
                "vector": vector_status,
                "elasticsearch": es_status,
                "redis": redis_status
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }