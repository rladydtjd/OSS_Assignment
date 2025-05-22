from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os # 파일 존재 여부 확인을 위해 os 모듈 임포트
from fastapi import FastAPI, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.requests import Request
import httpx
import xml.etree.ElementTree as ET

# summarize.py에서 정의한 라우터 가져오기
from app.routers.summarize import (
    router as summarize_router,
    summarize_news,
    SummarizeRequest
)
# FastAPI 앱 인스턴스 생성
app = FastAPI()

# 템플릿 파일 경로 설정 (HTML 파일을 'templates' 폴더에 두었다고 가정합니다)
templates = Jinja2Templates(directory="app/templates")

# CSV 파일 경로 (main_fastapi.py 파일과 같은 폴더에 있다고 가정합니다)
# 파일 이름은 '띠별_년생_운세수정버전.csv'입니다.
CSV_FILE_PATH = 'app/fortune.csv'
# 운세 데이터를 저장할 DataFrame 변수
fortune_df = None

# 앱 시작 시 CSV 파일을 로드하는 함수
# FastAPI의 startup 이벤트를 사용하면 앱이 시작될 때 데이터를 로드할 수 있습니다.
@app.on_event("startup")
async def load_data_on_startup():
    """앱 시작 시 운세 데이터를 로드합니다."""
    global fortune_df
    if not os.path.exists(CSV_FILE_PATH):
        print(f"!!! 경고: '{CSV_FILE_PATH}' 파일을 찾을 수 없습니다. 크롤링 코드를 먼저 실행하여 파일을 생성해주세요.")
        fortune_df = pd.DataFrame()
        return # 파일이 없으면 로드 중단

    try:
        # CSV 파일을 DataFrame으로 읽어옵니다.
        # header=None: CSV 파일에 헤더가 없음을 명시
        # encoding='euc-kr': 한글 깨짐 방지를 위해 사용 (CSV 파일 인코딩에 따라 변경 가능)
        # sep=',': 쉼표로 구분된 파일임을 명시
        # dtype={1: int}: 1번 컬럼(년도)을 정수형으로 명시적 지정
        fortune_df = pd.read_csv(CSV_FILE_PATH, encoding='euc-kr', sep=',', header=None, dtype={1: int})
        # 컬럼에 알기 쉬운 이름 지정 (데이터 형식: 띠, 년도, 운세내용)
        fortune_df.columns = ['띠', '년도', '운세내용']

        print("\n--- DataFrame 정보 ---")
        print(fortune_df.info())
        print("\n--- DataFrame 첫 5행 ---")
        print(fortune_df.head())
        print("---------------------\n")
        print(f"'{CSV_FILE_PATH}' 파일 로드 성공.")

    except Exception as e:
        print(f"!!! 오류: CSV 파일 로드 중 오류 발생: {e}")
        fortune_df = pd.DataFrame() # 오류 발생 시 빈 DataFrame 생성

# 루트 경로 - 메인 페이지 렌더링
# FastAPI에서는 Request 객체를 사용하여 요청 정보를 받을 수 있습니다.
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 'index.html' 파일을 렌더링합니다.
    # context에 request를 포함시켜야 템플릿에서 url_for 등의 함수를 사용할 수 있습니다.
    return templates.TemplateResponse("index.html", {"request": request})

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
    
# 운세 검색 API 요청 모델 정의 (Pydantic 사용)
class FortuneRequest(BaseModel):
    birth_year: int # 출생 연도는 숫자로 받도록 명시

# 운세 검색 API 엔드포인트
@app.post("/api/fortune")
async def get_fortune(request_data: FortuneRequest):
    birth_year_int = request_data.birth_year # Pydantic 모델에서 자동 형변환됨

    # DataFrame이 로드되지 않았거나 비어있으면 오류 반환
    if fortune_df is None or fortune_df.empty:
        # Flask의 500 에러에 해당
        raise HTTPException(status_code=500, detail='운세 데이터를 불러올 수 없습니다. CSV 파일을 확인해주세요.')

    try:
        # DataFrame에서 입력된 년도와 정확히 일치하는 행을 찾습니다.
        # '년도' 컬럼이 정수형으로 로드되었다고 가정합니다.
        found_fortunes = fortune_df[fortune_df['년도'] == birth_year_int]
    except KeyError:
         # 데이터 처리 오류: '년도' 컬럼을 찾을 수 없는 경우
         raise HTTPException(status_code=500, detail="데이터 처리 오류: '년도' 컬럼을 찾을 수 없습니다.")
    except Exception as e: # 예상치 못한 다른 pandas 관련 오류 처리
         print(f"DataFrame 검색 중 오류 발생: {e}")
         raise HTTPException(status_code=500, detail="운세 데이터를 검색하는 중 오류가 발생했습니다.")


    # 검색된 결과가 있는지 확인
    if not found_fortunes.empty:
        try:
            # 첫 번째로 찾은 결과 사용
            # 컬럼 이름 '띠'와 '운세내용'을 사용하여 데이터 가져오기
            띠 = found_fortunes.iloc[0]['띠']
            운세 = found_fortunes.iloc[0]['운세내용']
            # 프론트엔드에서 '운세' 키를 기대하므로, '운세내용' 값을 '운세' 키로 반환
            return {"띠": 띠, "운세": 운세} # dict 형태로 반환하면 JSON 응답
        except KeyError as e:
             # '띠' 또는 '운세내용' 컬럼이 없는 경우
             raise HTTPException(status_code=500, detail=f"데이터 형식 오류: 필요한 컬럼({e})이 CSV 파일에 없습니다.")
        except IndexError:
             # 데이터는 찾았지만 행이 비어있는 이상한 경우 (발생 가능성 낮음)
             raise HTTPException(status_code=500, detail="운세 데이터를 가져오는 중 예상치 못한 오류가 발생했습니다.")
    else:
        # 해당 년생의 운세가 없는 경우 (Flask의 404 에러에 해당)
        raise HTTPException(status_code=404, detail=f'{birth_year_int}년생의 운세 데이터를 찾을 수 없습니다.')

# 참고: FastAPI는 uvicorn으로 실행합니다. 아래 코드는 직접 실행 시 uvicorn 서버를 시작합니다.
# if __name__ == '__main__':
#     import uvicorn
#     # host를 '0.0.0.0'으로 설정하면 외부 접속 허용 (개발 시)
#     uvicorn.run(app, host='127.0.0.1', port=8000)
