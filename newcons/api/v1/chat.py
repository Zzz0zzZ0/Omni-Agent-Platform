"""POST /api/v1/chat"""
from fastapi import APIRouter, Depends, HTTPException

from api.schemas import ChatRequest, ChatResponse
from api.deps import get_chat_service
from services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    svc: ChatService = Depends(get_chat_service),
):
    try:
        result = await svc.chat(
            query=req.query,
            use_agent=req.use_agent,
            model_type=req.model_type,
            use_auto_alpha=req.use_auto_alpha,
            alpha=req.alpha,
            use_emotion=req.use_emotion,
            k_param=req.k_param,
            temp_param=req.temp_param,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
