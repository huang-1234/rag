from fastapi import APIRouter
from .rag import router as rag_router
from .ingest import router as ingest_router
from .sync import router as sync_router
from .health import router as health_router

api_router = APIRouter()

api_router.include_router(rag_router)
api_router.include_router(ingest_router)
api_router.include_router(sync_router)
api_router.include_router(health_router)