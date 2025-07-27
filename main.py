from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
import time
import os
from dotenv import load_dotenv
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 加载环境变量
load_dotenv()

# 导入API路由
from api.v1 import api_router

# 创建FastAPI应用
app = FastAPI(
    title="企业级RAG服务",
    description="基于混合检索技术的企业级RAG（检索增强生成）服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置Prometheus指标
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """收集请求指标的中间件"""
    start_time = time.time()

    # 处理请求
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        # 记录指标
        endpoint = request.url.path
        method = request.method

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)

    return response

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# 包含API路由
app.include_router(api_router)

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端HTML页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    # 启动服务器
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)