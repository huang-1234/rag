from typing import List, Dict, Any, Optional
import os
import uuid
from datetime import datetime
import hashlib

class DocumentProcessor:
    """文档处理服务，负责文档的分块和处理"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档处理器

        Args:
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process(self, content: str, file_type: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        处理文档内容

        Args:
            content: 文档内容
            file_type: 文件类型
            metadata: 元数据

        Returns:
            处理后的文档块列表
        """
        # 使用简单的文本分块策略
        chunks = self._split_text(content)

        # 生成基础元数据
        base_metadata = metadata or {}
        base_metadata.update({
            "file_type": file_type,
            "processed_at": datetime.now().isoformat(),
            "processor_version": "1.0.0"
        })

        # 为每个块添加元数据
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": i,
                "semantic_tag": self._detect_semantic_tag(chunk),
                "content_hash": self._hash_content(chunk)
            })

            result.append({
                "content": chunk,
                "metadata": chunk_metadata
            })

        return result

    def _split_text(self, text: str) -> List[str]:
        """
        将文本分割成块

        Args:
            text: 文本内容

        Returns:
            文本块列表
        """
        # 使用简单的分段策略
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        # 处理重叠
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i in range(len(chunks)):
                if i == 0:
                    overlapped_chunks.append(chunks[i])
                else:
                    # 从前一个块的末尾获取重叠内容
                    prev_chunk = chunks[i-1]
                    overlap_content = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                    overlapped_chunks.append(overlap_content + chunks[i])

            chunks = overlapped_chunks

        return chunks

    def _detect_semantic_tag(self, text: str) -> str:
        """
        检测文本的语义标签

        Args:
            text: 文本内容

        Returns:
            语义标签
        """
        # 简单的规则匹配
        if "```" in text or "代码" in text or "function" in text or "class" in text:
            return "code"
        elif "步骤" in text or "操作" in text or "1." in text or "2." in text:
            return "procedure"
        elif "注意" in text or "警告" in text or "!" in text:
            return "warning"
        elif "表格" in text or "数据" in text or "|" in text:
            return "data"
        else:
            return "general"

    def _hash_content(self, content: str) -> str:
        """
        计算内容哈希值

        Args:
            content: 文本内容

        Returns:
            哈希值
        """
        return hashlib.md5(content.encode()).hexdigest()