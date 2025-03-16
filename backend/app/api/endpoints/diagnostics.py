import time

import psutil
from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
    """シンプルな応答確認エンドポイント"""
    return {"status": "ok", "timestamp": time.time()}


@router.get("/system")
async def system_info():
    """システムリソース情報を返す"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "active_threads": len(psutil.Process().threads()),
    }
