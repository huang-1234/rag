import asyncio
import sys
import json
import time
from typing import List, Dict, Any

from services.retriever import HybridRetriever

async def main():
    """调试RAG查询"""
    if len(sys.argv) < 2:
        print("使用方法: python -m tasks.debug_rag \"您的查询\"")
        return

    query = sys.argv[1]
    print(f"执行查询: {query}")

    # 初始化检索器
    retriever = HybridRetriever()
    await retriever.initialize()

    # 执行检索
    start_time = time.time()
    results = await retriever.retrieve(query, top_k=5)
    elapsed = time.time() - start_time

    # 打印结果
    print(f"\n查询耗时: {elapsed*1000:.2f}ms")
    print(f"检索方法: {results[0]['search_method'] if results else 'hybrid'}")
    print(f"结果数量: {len(results)}")

    print("\n检索结果:")
    print("=" * 80)

    for i, result in enumerate(results):
        print(f"\n[{i+1}] 得分: {result['score']:.4f} | 来源: {result.get('source', 'unknown')}")
        print(f"标题: {result.get('metadata', {}).get('title', result.get('title', '无标题'))}")

        # 打印元数据
        metadata = result.get('metadata', {})
        if metadata:
            print("元数据:")
            for key, value in metadata.items():
                if key != 'title' and key != 'content':
                    print(f"  - {key}: {value}")

        # 打印内容摘要
        content = result.get('content', '')
        print(f"\n内容摘要:\n{content[:300]}...")
        print("-" * 80)

    print("\n详细信息:")
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())