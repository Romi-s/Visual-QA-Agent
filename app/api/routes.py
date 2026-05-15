import filetype
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agent.graph import qa_graph
from app.config import settings
from app.schemas.responses import QAResponse

router = APIRouter()

ALLOWED_MIMES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}


@router.post("/qa", response_model=QAResponse)
async def visual_qa(
    file: UploadFile = File(...),
    question: str = Form(...),
):
    file_bytes = await file.read()

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_file_size_mb} MB limit",
        )

    kind = filetype.guess(file_bytes)
    detected_mime = kind.mime if kind else "application/octet-stream"
    if detected_mime not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {detected_mime}",
        )

    initial_state = {
        "file_bytes": file_bytes,
        "file_mime": detected_mime,
        "question": question,
        "images": [],
        "page_count": 0,
        "answer": "",
        "error": None,
    }
    result = qa_graph.invoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return QAResponse(
        answer=result["answer"],
        page_count=result["page_count"],
        model=settings.active_model,
    )
