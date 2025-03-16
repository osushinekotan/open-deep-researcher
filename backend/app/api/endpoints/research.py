import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.research_manager import ResearchManager, get_research_manager
from app.models.research import PlanResponse, ResearchRequest, ResearchResponse, ResearchStatus

router = APIRouter()

# 進行中のリサーチを保存する辞書
research_tasks: dict[str, dict[str, Any]] = {}


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    research_manager: ResearchManager = Depends(get_research_manager),
):
    """新しいリサーチを開始"""
    research_id = str(uuid.uuid4())

    # バックグラウンドタスクとしてリサーチを実行
    background_tasks.add_task(
        research_manager.execute_research,
        research_id=research_id,
        topic=request.topic,
        config=request.config,
        user_id=request.user_id,  # ユーザーIDを渡す
    )

    return ResearchResponse(
        research_id=research_id,
        topic=request.topic,
        status="pending",
        message="リサーチタスクが作成されました。ステータスを確認するには /status/{research_id} にアクセスしてください。",
        user_id=request.user_id,
    )


@router.get("/{research_id}/status", response_model=ResearchStatus)
async def get_research_status(
    research_id: str,
    research_manager: ResearchManager = Depends(get_research_manager),  # noqa
):
    """リサーチの現在のステータスを取得"""
    status = await research_manager.get_research_status(research_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Research ID {research_id} not found")
    return status


@router.get("/{research_id}/plan", response_model=PlanResponse)
async def get_research_plan(
    research_id: str,
    research_manager: ResearchManager = Depends(get_research_manager),  # noqa
):
    """リサーチプランを取得（フィードバック用）"""
    plan = await research_manager.get_research_plan(research_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Research plan for ID {research_id} not found")
    return plan


@router.get("/{research_id}/result")
async def get_research_result(
    research_id: str,
    research_manager: ResearchManager = Depends(get_research_manager),  # noqa
):
    """完了したリサーチの結果を取得"""
    result = await research_manager.get_research_result(research_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Research result for ID {research_id} not found")
    return result


@router.get("/list", response_model=list[ResearchStatus])
async def list_researches(
    user_id: str | None = None,
    research_manager: ResearchManager = Depends(get_research_manager),
):
    """リサーチのリストを取得"""
    return await research_manager.list_researches(user_id=user_id)


@router.delete("/{research_id}")
async def delete_research(
    research_id: str,
    research_manager: ResearchManager = Depends(get_research_manager),  # noqa
):
    """リサーチを削除"""
    success = await research_manager.delete_research(research_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Research ID {research_id} not found")
    return {"message": f"Research {research_id} successfully deleted"}
