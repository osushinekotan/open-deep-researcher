from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.research_manager import ResearchManager, get_research_manager
from app.models.research import FeedbackRequest

router = APIRouter()


@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    research_manager: ResearchManager = Depends(get_research_manager),
):
    """リサーチプランに対するフィードバックを送信"""
    # フィードバック処理をバックグラウンドで実行
    background_tasks.add_task(
        research_manager.submit_feedback, research_id=feedback.research_id, feedback=feedback.feedback
    )

    if (feedback.feedback is None) or (feedback.feedback.strip() == ""):
        return {"message": "Plan approved. Research execution started."}
    else:
        return {"message": "Feedback submitted. Plan will be updated."}
