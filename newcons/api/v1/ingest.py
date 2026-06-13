"""POST /api/v1/ingest/*"""
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from api.deps import get_ingest_service
from services.ingest_service import IngestService

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    svc: IngestService = Depends(get_ingest_service),
):
    try:
        return await svc.ingest_document(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def ingest_feedback(
    svc: IngestService = Depends(get_ingest_service),
    feedback_text: str = Form(None),
    doc_file: UploadFile = File(None),
    images: List[UploadFile] = File([]),
):
    try:
        return await svc.ingest_feedback(feedback_text, doc_file, images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
