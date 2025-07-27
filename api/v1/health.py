from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import os
import psutil
import platform
from datetime import datetime, timedelta

from services.vector import get_vector_service
from services.retriever import HybridRetriever

router = APIRouter(prefix="/v1/health", tags=["Health Monitoring"])

# 存储性能指标历史
metrics_history = {
    "total_docs": [],
    "today_updates": [],
    "success_rate": [],
    "avg_response": []
}

# 模拟数据
last_update = datetime.now()
total_docs = 12458
today_updates = 142
success_rate = 0.987
avg_response = 286

@router.get(
    "",
    summary="获取服务健康状态",
    responses={
        200: {"description": "返回服务健康状态"},
        500: {"description": "服务异常"}
    }
)
async def get_health():
    """
    获取RAG服务的健康状态和关键指标
    """
    global last_update, total_docs, today_updates, success_rate, avg_response

    try:
        # 模拟数据更新
        current_time = datetime.now()
        if (current_time - last_update).total_seconds() > 60:
            # 每分钟更新一次模拟数据
            total_docs += int(5 * (0.5 + 0.5 * (time.time() % 10) / 10))
            today_updates = int(today_updates * 1.01)
            success_rate = min(0.999, success_rate + 0.001 * (time.time() % 3 - 1))
            avg_response = max(100, avg_response - 1 + int(5 * (time.time() % 3 - 1)))
            last_update = current_time

        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "platform": platform.platform(),
                "python_version": platform.python_version()
            },
            "metrics": {
                "total_docs": total_docs,
                "today_updates": today_updates,
                "success_rate": success_rate,
                "avg_response": avg_response
            },
            "services": await check_services()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get(
    "/metrics",
    summary="获取服务指标",
    responses={
        200: {"description": "返回服务指标"}
    }
)
async def get_metrics():
    """
    获取RAG服务的性能指标
    """
    global total_docs, today_updates, success_rate, avg_response

    # 更新历史数据
    current_time = datetime.now().isoformat()
    metrics_history["total_docs"].append({"time": current_time, "value": total_docs})
    metrics_history["today_updates"].append({"time": current_time, "value": today_updates})
    metrics_history["success_rate"].append({"time": current_time, "value": success_rate})
    metrics_history["avg_response"].append({"time": current_time, "value": avg_response})

    # 只保留最近100个数据点
    for key in metrics_history:
        if len(metrics_history[key]) > 100:
            metrics_history[key] = metrics_history[key][-100:]

    return {
        "current": {
            "total_docs": total_docs,
            "today_updates": today_updates,
            "success_rate": success_rate,
            "avg_response": avg_response
        },
        "history": metrics_history
    }

@router.get(
    "/services",
    summary="获取服务状态",
    responses={
        200: {"description": "返回各服务状态"}
    }
)
async def get_services_status():
    """
    获取各个依赖服务的状态
    """
    return await check_services()

async def check_services() -> Dict[str, Any]:
    """
    检查各个依赖服务的状态

    Returns:
        服务状态字典
    """
    services = {}

    # 检查向量服务
    try:
        vector_service = get_vector_service()
        # 简单查询测试
        await vector_service.search("test", top_k=1)
        services["vector"] = {
            "status": "ok",
            "latency": 10  # 模拟延迟
        }
    except Exception as e:
        services["vector"] = {
            "status": "error",
            "error": str(e)
        }

    # 检查Elasticsearch
    try:
        retriever = HybridRetriever()
        await retriever.es.info()
        services["elasticsearch"] = {
            "status": "ok",
            "latency": 15  # 模拟延迟
        }
    except Exception as e:
        services["elasticsearch"] = {
            "status": "error",
            "error": str(e)
        }

    # 检查Redis
    try:
        retriever = HybridRetriever()
        await retriever.redis.ping()
        services["redis"] = {
            "status": "ok",
            "latency": 5  # 模拟延迟
        }
    except Exception as e:
        services["redis"] = {
            "status": "error",
            "error": str(e)
        }

    return services