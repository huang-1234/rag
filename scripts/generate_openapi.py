import json
import os
from main import app

def main():
    """生成OpenAPI文档"""
    print("正在生成OpenAPI文档...")

    # 获取OpenAPI模式
    openapi_schema = app.openapi()

    # 添加自定义信息
    openapi_schema["info"]["title"] = "企业级RAG服务API"
    openapi_schema["info"]["description"] = "基于混合检索技术的企业级RAG（检索增强生成）服务API"
    openapi_schema["info"]["version"] = "1.0.0"
    openapi_schema["info"]["contact"] = {
        "name": "RAG团队",
        "email": "rag@example.com"
    }

    # 保存为JSON文件
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)

    print(f"OpenAPI文档已生成: {os.path.abspath('openapi.json')}")

    # 生成HTML文档
    try:
        import yaml

        # 转换为YAML格式
        with open("openapi.yaml", "w", encoding="utf-8") as f:
            yaml.dump(openapi_schema, f, allow_unicode=True)

        print(f"OpenAPI YAML文档已生成: {os.path.abspath('openapi.yaml')}")

        # 生成HTML文档
        try:
            os.system("npx redoc-cli bundle openapi.yaml -o openapi.html")
            print(f"HTML文档已生成: {os.path.abspath('openapi.html')}")
        except Exception as e:
            print(f"生成HTML文档失败: {e}")
            print("提示: 您可以安装redoc-cli来生成HTML文档: npm install -g redoc-cli")
    except ImportError:
        print("未安装PyYAML，跳过YAML和HTML文档生成")
        print("提示: 您可以安装PyYAML: pip install pyyaml")

if __name__ == "__main__":
    main()