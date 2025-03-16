import asyncio
import time

import psutil
from fastapi import APIRouter, BackgroundTasks

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


# 応答時間をシミュレートするためのエンドポイント
@router.get("/latency/{delay_ms}")
async def test_latency(delay_ms: int, background_tasks: BackgroundTasks):
    """指定されたミリ秒の遅延後に応答するエンドポイント"""
    if delay_ms <= 0:
        return {"latency": 0}

    # 短い遅延は直接処理
    if delay_ms < 100:
        await asyncio.sleep(delay_ms / 1000)
        return {"latency": delay_ms}

    # 長い遅延はバックグラウンドタスクとして処理し、すぐに応答
    async def long_task():
        await asyncio.sleep(delay_ms / 1000)

    background_tasks.add_task(long_task)
    return {"latency": f"{delay_ms}ms (background)"}
