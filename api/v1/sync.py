from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import asyncio
import time
import json
from datetime import datetime

router = APIRouter(prefix="/v1/sync", tags=["Document Synchronization"])

# 存储活跃的WebSocket连接
active_connections: List[WebSocket] = []

# 同步状态存储
sync_status = {}

async def broadcast_status(source_id: str, status: Dict[str, Any]):
    """
    广播同步状态更新

    Args:
        source_id: 文档源ID
        status: 状态信息
    """
    # 更新状态存储
    sync_status[source_id] = status

    # 广播给所有连接
    for connection in active_connections:
        try:
            await connection.send_json({
                "source_id": source_id,
                **status
            })
        except Exception:
            pass

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，用于实时同步状态更新
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "initial_status",
            "status": sync_status
        })

        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端消息，例如请求特定源的状态
            try:
                msg = json.loads(data)
                if msg.get("action") == "get_status" and "source_id" in msg:
                    source_id = msg["source_id"]
                    if source_id in sync_status:
                        await websocket.send_json({
                            "type": "status_update",
                            "source_id": source_id,
                            **sync_status[source_id]
                        })
            except:
                pass

    except WebSocketDisconnect:
        active_connections.remove(websocket)

@router.post(
    "/start/{source_id}",
    summary="开始同步文档源",
    responses={
        202: {"description": "同步任务已启动"},
        404: {"description": "文档源不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def start_sync(
    source_id: str,
    background_tasks: BackgroundTasks
):
    """
    开始同步指定的文档源

    - **source_id**: 文档源ID
    """
    # 这里应该检查文档源是否存在
    # 为了示例，我们假设它存在

    # 更新同步状态
    await broadcast_status(source_id, {
        "status": "processing",
        "progress": 0,
        "started_at": datetime.now().isoformat(),
        "message": "同步任务已启动"
    })

    # 添加后台任务
    background_tasks.add_task(
        simulate_sync_process,
        source_id
    )

    return {
        "status": "accepted",
        "message": "同步任务已启动",
        "source_id": source_id,
        "timestamp": time.time()
    }

@router.get(
    "/status/{source_id}",
    summary="获取同步状态",
    responses={
        200: {"description": "返回同步状态"},
        404: {"description": "文档源不存在或未开始同步"}
    }
)
async def get_sync_status(source_id: str):
    """
    获取指定文档源的同步状态

    - **source_id**: 文档源ID
    """
    if source_id not in sync_status:
        raise HTTPException(status_code=404, detail="文档源不存在或未开始同步")

    return {
        "source_id": source_id,
        **sync_status[source_id]
    }

@router.get(
    "/all",
    summary="获取所有同步状态",
    responses={
        200: {"description": "返回所有同步状态"}
    }
)
async def get_all_sync_status():
    """
    获取所有文档源的同步状态
    """
    return sync_status

async def simulate_sync_process(source_id: str):
    """
    模拟同步过程

    Args:
        source_id: 文档源ID
    """
    # 模拟同步过程
    for progress in range(0, 101, 10):
        await broadcast_status(source_id, {
            "status": "processing" if progress < 100 else "completed",
            "progress": progress,
            "message": f"同步进度: {progress}%" if progress < 100 else "同步完成",
            "updated_at": datetime.now().isoformat()
        })

        # 模拟处理时间
        await asyncio.sleep(1)

    # 更新最终状态
    await broadcast_status(source_id, {
        "status": "completed",
        "progress": 100,
        "message": "同步完成",
        "completed_at": datetime.now().isoformat()
    })