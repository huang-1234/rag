from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import time
import json
import uuid
from datetime import datetime

from services.document_processor import DocumentProcessor
from services.vector import VectorService, get_vector_service
from models.document import DocumentUploadRequest, DocumentMetadata

router = APIRouter(prefix="/v1/ingest", tags=["Document Ingestion"])

# 初始化服务
processor = DocumentProcessor()
vector_service = get_vector_service()

async def process_document(content: str, file_type: str, metadata: Dict[str, Any]):
    """
    后台处理文档

    Args:
        content: 文档内容
        file_type: 文件类型
        metadata: 元数据
    """
    # 处理文档
    chunks = processor.process(content, file_type, metadata)

    # 提取文本和元数据
    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    # 生成向量
    vectors = await vector_service.encode_async(texts)

    # 存储向量
    await vector_service.upsert(
        vectors=vectors,
        payloads=[{
            "content": text,
            **metadata
        } for text, metadata in zip(texts, metadatas)]
    )

    print(f"文档处理完成，共 {len(chunks)} 个块")

@router.post(
    "/upload",
    summary="上传并处理文档",
    responses={
        202: {"description": "文档已接收并开始处理"},
        400: {"description": "无效请求参数"},
        500: {"description": "服务器内部错误"}
    }
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    source_type: str = Form("manual"),
    source_id: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """
    上传并处理文档

    - **file**: 文档文件
    - **title**: 文档标题
    - **source_type**: 文档来源类型
    - **source_id**: 文档来源ID
    - **author**: 作者
    - **tags**: 标签（逗号分隔）
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 解析文件类型
        file_type = file.filename.split(".")[-1] if "." in file.filename else "txt"

        # 准备元数据
        metadata = {
            "title": title,
            "source_type": source_type,
            "file_name": file.filename,
            "file_type": file_type,
            "processed_at": datetime.now().isoformat(),
            "doc_id": str(uuid.uuid4())
        }

        if source_id:
            metadata["source_id"] = source_id

        if author:
            metadata["author"] = author

        if tags:
            metadata["tags"] = [tag.strip() for tag in tags.split(",")]

        # 添加后台任务
        background_tasks.add_task(
            process_document,
            content.decode("utf-8", errors="ignore"),
            file_type,
            metadata
        )

        return {
            "status": "accepted",
            "message": "文档已接收并开始处理",
            "doc_id": metadata["doc_id"],
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@router.post(
    "/text",
    summary="直接提交文本内容",
    responses={
        202: {"description": "文档已接收并开始处理"},
        400: {"description": "无效请求参数"},
        500: {"description": "服务器内部错误"}
    }
)
async def upload_text(
    background_tasks: BackgroundTasks,
    request: DocumentUploadRequest = Body(...)
):
    """
    直接提交文本内容

    - **title**: 文档标题
    - **content**: 文档内容
    - **metadata**: 元数据
    - **source_type**: 文档来源类型
    - **source_id**: 文档来源ID
    """
    try:
        # 准备元数据
        metadata = request.metadata.dict() if request.metadata else {}
        metadata.update({
            "title": request.title,
            "source_type": request.source_type,
            "processed_at": datetime.now().isoformat(),
            "doc_id": str(uuid.uuid4())
        })

        if request.source_id:
            metadata["source_id"] = request.source_id

        # 添加后台任务
        background_tasks.add_task(
            process_document,
            request.content,
            "txt",
            metadata
        )

        return {
            "status": "accepted",
            "message": "文档已接收并开始处理",
            "doc_id": metadata["doc_id"],
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")