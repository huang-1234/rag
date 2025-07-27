from cursor import command, script
import os
import sys
import asyncio

@command
def dev_setup():
    """初始化开发环境"""
    script.run("pip install -r requirements.txt")
    script.run("mkdir -p data/qdrant data/elasticsearch data/redis")
    script.run("docker-compose up -d qdrant elasticsearch redis")
    print("开发环境已准备就绪")

@command
def start_dev():
    """启动开发服务器"""
    script.run("uvicorn main:app --reload --host 0.0.0.0 --port 8000")

@command
def ingest_sample_data():
    """导入示例数据"""
    script.run("python -m tasks.ingest_samples")
    print("示例数据导入完成")

@command
def debug_rag(query: str):
    """调试RAG查询"""
    script.run(f"python -m tasks.debug_rag \"{query}\"")

@command
def generate_openapi():
    """生成OpenAPI文档"""
    script.run("python -m scripts.generate_openapi")
    print("OpenAPI文档已生成: openapi.json")

@command
def run_tests():
    """运行测试"""
    script.run("pytest tests/")

@command
def build_docker():
    """构建Docker镜像"""
    script.run("docker-compose build")

@command
def deploy():
    """部署服务"""
    script.run("docker-compose up -d")