from fastapi import APIRouter, Form
from pydantic import BaseModel, HttpUrl
import pandas as pd
import os
from .processor import process_url

router = APIRouter()

class SummarizeRequest(BaseModel):
    url: HttpUrl

class SummarizeResponse(BaseModel):
    summary: str

CSV_SAVE_PATH = "../../summaries.csv"

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_news(req: SummarizeRequest):
    # 받은 URL을 processor.py에 있는 함수로 처리
    processed_result = process_url(str(req.url))

    # CSV에 저장 (기존 내용이 있다면 추가)
    df_new = pd.DataFrame([{"url": str(req.url), "summary": processed_result}])
    if os.path.exists(CSV_SAVE_PATH):
        df_old = pd.read_csv(CSV_SAVE_PATH)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv(CSV_SAVE_PATH, index=False)
    else:
        df_new.to_csv(CSV_SAVE_PATH, index=False)

    # 처리된 결과를 바로 반환 (웹페이지에 출력됨)
    return SummarizeResponse(summary=processed_result)

@router.post("/summarize-form", response_model=SummarizeResponse)
async def summarize_form(url: str = Form(...)):
    return await summarize_news(SummarizeRequest(url=url))
