from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

# 요약 기능과 라우터 가져오기
from app.routers.summarize import router as summarize_router, summarize_news, SummarizeRequest

app = FastAPI(title="OSS개론")

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 요약 API 라우터 등록 (/api/summarize 등)
app.include_router(summarize_router, prefix="/api")

# GET / — 메인 페이지 렌더링
@app.get("/", response_class=templates.TemplateResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# POST / — 폼 제출 처리, 요약 결과를 같은 템플릿에 렌더링
@app.post("/", response_class=templates.TemplateResponse)
async def index_post(request: Request, url: str = Form(...)):
    # 더미 또는 실제 요약 호출
    resp = await summarize_news(SummarizeRequest(url=url))
    # 요약 박스 표시 플래그 전달
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "summary": resp.summary,
            "show_summary": True
        }
    )
