# app/routers/summarize.py

from fastapi import APIRouter, Form
from pydantic import BaseModel, HttpUrl

router = APIRouter()

class SummarizeRequest(BaseModel):
    url: HttpUrl

class SummarizeResponse(BaseModel):
    summary: str

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_news(req: SummarizeRequest):
    # 테스트용 더미 요약만 반환
    return SummarizeResponse(
        summary=f"[테스트용 더미 요약]\n입력된 URL: {req.url}"
    )

@router.post("/summarize-form", response_model=SummarizeResponse)
async def summarize_form(url: str = Form(...)):
    # HTML 폼 전송 지원 (동일하게 동작)
    return await summarize_news(SummarizeRequest(url=url))
