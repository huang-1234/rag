from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class DocumentMetadata(BaseModel):
    """文档元数据模型"""
    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    file_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    """文档块模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chunk_index: Optional[int] = None
    semantic_tag: Optional[str] = None
    content_hash: Optional[str] = None
    embedding: Optional[List[float]] = None

class Document(BaseModel):
    """完整文档模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chunks: List[DocumentChunk] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DocumentSource(BaseModel):
    """文档源模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source_type: str  # 例如：file, web, github, feishu等
    config: Dict[str, Any] = Field(default_factory=dict)
    credentials: Dict[str, Any] = Field(default_factory=dict)
    sync_status: str = "pending"  # pending, syncing, completed, failed
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RAGRequest(BaseModel):
    """RAG查询请求模型"""
    query: str
    top_k: int = 5
    temperature: float = 0.7
    use_cache: bool = True
    filters: Optional[Dict[str, Any]] = None

class RAGResponse(BaseModel):
    """RAG查询响应模型"""
    results: List[Dict[str, Any]]
    latency: float
    search_method: str

class DocumentUploadRequest(BaseModel):
    """文档上传请求模型"""
    title: str
    content: str
    metadata: Optional[DocumentMetadata] = None
    source_type: str = "manual"
    source_id: Optional[str] = None