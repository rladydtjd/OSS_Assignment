# NewsTopicA v1.0.0

**KoBERT** 기반 뉴스 요약 시스템  
URL만 붙여넣으면 뉴스 내용을 요약하여 빠르게 확인할 수 있습니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![KoBERT](https://img.shields.io/badge/KoBERT-transformers-green)
![FastAPI](https://img.shields.io/badge/FastAPI-async%20web%20framework-009688)
![Status](https://img.shields.io/badge/status-beta-orange)


## 📌 소개

NewsTopicA(뉴스토픽아)는 사용자가 뉴스 기사 URL을 입력하면,  
해당 뉴스 내용을 자동으로 크롤링하고 **KoBERT 모델을 통해 요약**하여 보여주는 시스템입니다.  
앞으로는 **날씨 정보**, **지역 관련 데이터**, **키워드 추출**, **감정 분석** 등의 기능도 추가할 예정입니다.


## ✨ 주요 기능

- 📄 **뉴스 URL 자동 크롤링**
- 🤖 **KoBERT 기반 텍스트 요약**
- 🧠 **한눈에 보기 쉬운 요약 결과 제공**
- 📌 추후 기능 확장 예정:
  - 현재 지역의 **날씨 정보 연동**
  - 관련 **이슈 키워드 추출**
  - **감정 분석**, **토픽 클러스터링** 등


## 🔧 기술 스택

| 범주 | 기술 |
|------|------|
| 언어 | Python 3.11|
| 딥러닝 모델 | KoBERT (KakaoBrain) |
| 웹 프레임워크 | FastAPI |
| 웹 크롤링 | BeautifulSoup, requests |
| 요약 방법 | KoBERT + 텍스트 전처리 |
| 배포 예정 | FastAPI |


## 🚀 시작하기

```bash
# 1. 클론
git clone https://github.com/your-username/NewsTopicA.git
cd NewsTopicA

# 2. 가상환경 생성 및 패키지 설치
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate (on Windows)
pip install -r requirements.txt

# 3. 실행
uvicorn app.main:app --reload
