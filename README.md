# 企业级RAG服务系统

基于混合检索技术的企业级RAG（检索增强生成）服务系统，支持多源文档处理、混合检索和高性能向量搜索。

## 主要特性

- 分层服务架构设计
- 混合检索（向量 + 关键词）
- 多源文档处理与同步
- 实时监控与性能优化
- 企业级部署支持

## 技术栈

- FastAPI: Web服务框架
- Qdrant: 向量数据库
- Elasticsearch: 关键词检索
- Redis: 缓存层
- SentenceTransformers: 文本向量化

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000

# 访问API文档
# http://localhost:8000/docs
```
