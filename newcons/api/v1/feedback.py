"""POST /api/v1/feedback/*"""
from fastapi import APIRouter, Depends, HTTPException

from api.schemas import RecommendationFeedback
from api.deps import get_ticket_service
from services.ticket_service import TicketService

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("/recommendation")
async def recommendation_reward(
    req: RecommendationFeedback,
    svc: TicketService = Depends(get_ticket_service),
):
    try:
        return await svc.update_recommendation_reward(req.arm_idx, req.context_vec, req.reward)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
