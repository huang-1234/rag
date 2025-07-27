import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any

from services.vector import get_vector_service
from services.document_processor import DocumentProcessor

# 示例文档
SAMPLE_DOCS = [
    {
        "title": "RAG系统介绍",
        "content": """
# 检索增强生成（RAG）系统

检索增强生成（Retrieval-Augmented Generation，RAG）是一种结合了检索系统和生成式AI的技术架构。它通过在生成回答前先检索相关信息，从而提高生成内容的准确性和可靠性。

## 核心组件

1. **文档处理流水线**：负责将各种格式的文档转换为可检索的向量表示。
2. **向量数据库**：存储文档的向量表示，支持高效的相似度搜索。
3. **检索系统**：根据用户查询找到最相关的文档片段。
4. **生成模型**：基于检索到的信息和用户查询生成回答。

## 优势

- 提高回答的准确性和可靠性
- 减少幻觉（生成虚假信息）
- 能够访问专有知识和最新信息
- 提供可追溯的信息来源

## 应用场景

- 企业知识库问答
- 客户支持系统
- 技术文档查询
- 研究辅助工具
        """,
        "metadata": {
            "author": "RAG团队",
            "tags": ["RAG", "介绍", "技术架构"],
            "created_date": "2023-09-01"
        }
    },
    {
        "title": "向量数据库比较",
        "content": """
# 向量数据库比较

向量数据库是RAG系统的核心组件，负责存储和检索文档的向量表示。本文比较几种流行的向量数据库。

## Qdrant

Qdrant是一个高性能的向量相似度搜索引擎，具有以下特点：

- 完全开源
- 支持过滤条件的向量搜索
- 提供REST API和gRPC接口
- 支持多种距离度量方式
- 可水平扩展

## Pinecone

Pinecone是一个托管的向量数据库服务，具有以下特点：

- 全托管SaaS解决方案
- 自动扩展
- 高可用性
- 简单的API
- 支持实时更新

## Milvus

Milvus是一个开源的向量数据库，具有以下特点：

- 高性能（每秒可处理数百万查询）
- 支持多种索引类型
- 水平扩展
- 混合搜索（向量+关键词）
- 云原生架构

## PGVector

PostgreSQL的向量扩展，具有以下特点：

- 与PostgreSQL生态系统集成
- 支持多种向量索引
- 可与关系数据结合使用
- 开源且成熟
- 适合中小规模应用

## 选择建议

- 对于开发和小型部署，Qdrant是一个很好的选择
- 对于无需运维的解决方案，可以考虑Pinecone
- 对于大规模部署，Milvus提供了更多的扩展选项
- 如果已经使用PostgreSQL，PGVector是自然的选择
        """,
        "metadata": {
            "author": "数据库团队",
            "tags": ["向量数据库", "Qdrant", "Pinecone", "Milvus", "PGVector"],
            "created_date": "2023-09-15"
        }
    },
    {
        "title": "混合检索策略",
        "content": """
# 混合检索策略

在RAG系统中，混合检索策略可以显著提高检索质量。本文介绍几种常用的混合检索方法。

## 关键词检索 + 向量检索

结合传统的关键词检索（如BM25）和现代的向量检索，可以兼顾精确匹配和语义相关性。

```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever

vector_retriever = vector_db.as_retriever(search_kwargs={"k": 5})
keyword_retriever = BM25Retriever.from_texts(texts)

ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, keyword_retriever],
    weights=[0.7, 0.3]
)
```

## 重排序策略

先使用高召回但低精度的方法检索大量候选文档，然后使用更精确但计算成本更高的方法重新排序。

```python
def rerank_results(query, candidates, reranker):
    # 对候选文档进行重排序
    scores = reranker.predict([(query, doc.content) for doc in candidates])
    ranked_results = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked_results]
```

## 多查询扩展

通过生成多个不同表述的查询来增加召回率。

```python
def generate_queries(original_query, llm):
    prompt = f"请用5种不同的方式重新表述以下问题: {original_query}"
    response = llm.predict(prompt)
    return [original_query] + response.split("\n")

def multi_query_retrieval(query, retriever, llm):
    queries = generate_queries(query, llm)
    all_docs = []
    for q in queries:
        docs = retriever.retrieve(q)
        all_docs.extend(docs)
    # 去重并返回
    return list(set(all_docs))
```

## 层次化检索

先检索相关文档集合，然后在这些文档中进行更细粒度的检索。

```python
def hierarchical_retrieval(query, corpus_retriever, doc_retriever):
    # 第一阶段：检索相关文档集
    relevant_corpora = corpus_retriever.retrieve(query)

    # 第二阶段：在相关文档中检索具体段落
    all_passages = []
    for corpus in relevant_corpora:
        passages = doc_retriever.retrieve(query, corpus=corpus)
        all_passages.extend(passages)

    return all_passages
```

## 融合策略

不同的检索方法可以通过多种方式融合结果：

1. **RRF (Reciprocal Rank Fusion)**：基于排名的融合方法
2. **线性组合**：对不同方法的分数进行加权平均
3. **投票法**：根据在不同方法中出现的频率排序
4. **学习排序**：使用机器学习模型学习最佳排序

选择适合的混合检索策略可以显著提高RAG系统的性能。
        """,
        "metadata": {
            "author": "检索团队",
            "tags": ["混合检索", "重排序", "多查询", "融合策略"],
            "created_date": "2023-10-01"
        }
    }
]

async def main():
    """导入示例文档"""
    print("开始导入示例文档...")

    # 初始化服务
    vector_service = get_vector_service()
    processor = DocumentProcessor()

    # 创建集合
    try:
        vector_service.create_collection("docs")
        print("创建向量集合成功")
    except Exception as e:
        print(f"创建集合失败（可能已存在）: {e}")

    # 处理并导入文档
    for i, doc in enumerate(SAMPLE_DOCS):
        print(f"处理文档 {i+1}/{len(SAMPLE_DOCS)}: {doc['title']}")

        # 处理文档
        chunks = processor.process(
            doc["content"],
            "md",
            {**doc["metadata"], "title": doc["title"]}
        )

        # 提取文本和元数据
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # 生成向量
        vectors = await vector_service.encode_async(texts)

        # 存储向量
        success = await vector_service.upsert(
            vectors=vectors,
            payloads=[{
                "content": text,
                "title": doc["title"],
                **metadata
            } for text, metadata in zip(texts, metadatas)]
        )

        if success:
            print(f"  - 成功导入 {len(chunks)} 个块")
        else:
            print(f"  - 导入失败")

    print("示例文档导入完成")

if __name__ == "__main__":
    asyncio.run(main())