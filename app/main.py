# app/main.py

from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.requests import Request

# 요약 기능과 라우터 가져오기
from app.routers.summarize import router as summarize_router, summarize_news, SummarizeRequest

app = FastAPI(title="OSS개론")

# 1) 정적 파일 서빙
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 2) 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="app/templates")

# 3) 파비콘 직접 처리 (브라우저가 /favicon.ico 요청 시)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/images/favicon.ico")

# 4) 요약 API 라우터 등록 (/api/summarize 등)
app.include_router(summarize_router, prefix="/api")

# 5) 메인 페이지 (GET /)
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 6) 폼 제출 처리 (POST /)
@app.post("/")
async def index_post(request: Request, url: str = Form(...)):
    # 요약 호출
    resp = await summarize_news(SummarizeRequest(url=url))
    # 요약 결과를 템플릿에 전달
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "summary": resp.summary
        }
    )
