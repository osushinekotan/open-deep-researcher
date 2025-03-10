from fastapi import APIRouter, Depends, HTTPException

from app.core.research_manager import ResearchManager, get_research_manager
from app.models.research import FeedbackRequest

router = APIRouter()


@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackRequest,
    research_manager: ResearchManager = Depends(get_research_manager),  # noqa
):
    """リサーチプランに対するフィードバックを送信"""
    success = await research_manager.submit_feedback(research_id=feedback.research_id, feedback=feedback.feedback)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Research ID {feedback.research_id} not found or not waiting for feedback"
        )

    if (feedback.feedback is None) or (feedback.feedback.strip() == ""):
        return {"message": "Plan approved. Research execution started."}
    else:
        return {"message": "Feedback submitted. Plan will be updated."}
