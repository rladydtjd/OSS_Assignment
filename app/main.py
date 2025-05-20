from fastapi import FastAPI, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.requests import Request
import httpx
import xml.etree.ElementTree as ET

# 요약 기능과 라우터 가져오기
from app.routers.summarize import (
    router as summarize_router,
    summarize_news,
    SummarizeRequest
)

app = FastAPI(title="OSS개론")

# 1) 정적 파일 서빙
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# 2) 템플릿 디렉토리 설정
templates = Jinja2Templates(directory="app/templates")

# 3) 파비콘 처리
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/images/favicon.ico")

# 4) 요약 API 라우터 등록
app.include_router(summarize_router, prefix="/api")

# 5) 실시간 인기 뉴스 RSS 파싱 엔드포인트
@app.get("/api/trending-news")
async def trending_news(top_n: int = 5):
    """
    JTBC 이슈 RSS 피드에서 상위 top_n개 뉴스 제목을 가져옵니다.
    """
    RSS_URL = "https://news-ex.jtbc.co.kr/v1/get/rss/issue"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(RSS_URL)
            res.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"RSS 호출 실패: {e}")

    try:
        root = ET.fromstring(res.text)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        trending = []
        for item in items[:top_n]:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                trending.append({"title": title_el.text})
        return {"trending": trending}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RSS 파싱 실패: {e}")

# 6) 메인 페이지 (GET /)
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 7) 폼 제출 처리 (POST /)
@app.post("/")
async def index_post(request: Request, url: str = Form(...)):
    resp = await summarize_news(SummarizeRequest(url=url))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "summary": resp.summary
        }
    )
