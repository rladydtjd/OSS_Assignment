# processor.py
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urlparse, parse_qs
import os


def process_url(url: str) -> str:
    print('함수 시작')
    # URL을 받아서 뭔가 처리 후 문자열 결과 리턴
    # --- YTN 메인 메뉴 HTML 스니펫 (제공해주신 내용) ---
# 이 HTML을 파싱하여 카테고리 맵을 생성합니다.
    ytn_menu_html_snippet = """
                    <ul class="menu">
                        <li class="YTN_CSA_mainpolitics menu_election2025">
                            <a href="https://www.ytn.co.kr/issue/election2025">대선2025</a>
                        </li>
                        <li class="YTN_CSA_mainpolitics ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0101">정치</a>
                        </li>
                        <li class="YTN_CSA_maineconomy ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0102">경제</a>
                        </li>
                        <li class="YTN_CSA_mainsociety ">
                            <a href="https://www.ytn
                            .co.kr/news/list.php?mcd=0103">사회</a>
                        </li>
                        <li class="YTN_CSA_mainnationwide ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0115">전국</a>
                        </li>
                        <li class="YTN_CSA_mainglobal ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0104">국제</a>
                        </li>
                        <li class="YTN_CSA_mainscience ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0105">과학</a>
                        </li>
                        <li class="YTN_CSA_mainculture ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0106">문화</a>
                        </li>
                        <li class="YTN_CSA_mainsports ">
                            <a href="https://www.ytn.co.kr/news/list.php?mcd=0107">스포츠</a>
                        </li>
                        <li class="YTN_CSA_mainphoto ">
                            <a href="https://star.ytn.co.kr">연예</a>
                        </li>
                        <li class="YTN_CSA_maingame ">
                            <!--<a href="https://game.ytn.co.kr/news/list.php?mcd=0135">게임</a>-->
                            <a href="https://game.ytn.co.kr">게임</a>
                        </li>
                        <li class="YTN_CSA_mainweather ">
                            <a href="https://www.ytn.co.kr/weather/list_weather.php">날씨</a>
                        </li>
                        <li class="YTN_CSA_mainissue ">
                            <a href="https://www.ytn.co.kr/news/main_issue.html">이슈</a>
                        </li>
                        <li class="YTN_CSA_mainyp ">
                            <a href="https://www.ytn.co.kr/news/main_yp.html">시리즈</a>
                        </li>
                        <li class="YTN_CSA_mainreplay "><a href="https://www.ytn.co.kr/replay/main.html">TV프로그램</a></li>
                    </ul>
    """
    # --- 메뉴 HTML 파싱 및 카테고리 맵 생성 ---
    ytn_menu_soup = BeautifulSoup(ytn_menu_html_snippet, 'html.parser')
    ytn_category_map = {} # 카테고리 맵 초기화
    # 메뉴 HTML에서 a 태그들을 찾습니다.
    menu_links = ytn_menu_soup.select('ul.menu a')

    for link in menu_links:
        href = link.get('href')
        text = link.get_text(strip=True)
        if href and text:
            parsed_url = urlparse(href)
            # URL 경로가 '/news/list.php'이고 쿼리 스트링에 'mcd' 파라미터가 있는 경우
            if parsed_url.path == '/news/list.php' and parsed_url.query:
                query_params = parse_qs(parsed_url.query)
                if 'mcd' in query_params and query_params['mcd'][0]:
                    mcd_code = query_params['mcd'][0]
                    ytn_category_map[mcd_code] = text # mcd 코드를 키로, 카테고리 이름을 값으로 저장
                    # print(f"맵핑 추가: {mcd_code} -> {text}") # 디버깅용 출력

    # 생성된 카테고리 맵 확인 (선택 사항)
    print("--- 생성된 YTN 카테고리 맵 ---")
    print(ytn_category_map)
    print("-" * 30)
    def classify_ytn_category_from_url(url, category_map):
        """
        YTN 기사 URL 경로를 분석하여 카테고리 코드를 추출하고 맵핑된 카테고리 이름을 반환합니다.
        생성된 category_map을 사용합니다.
        """
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path # 예: '/_ln/0103_202505111017133914'
            path_segments = path.split('/')
            
            if '_ln' in path_segments:
                ln_index = path_segments.index('_ln')
                if ln_index + 1 < len(path_segments):
                    # 예: '0103_202505111017133914'
                    code_segment = path_segments[ln_index + 1]
                    # 코드 세그먼트에서 첫 번째 '_' 이전 부분이 카테고리 코드입니다.
                    code = code_segment.split('_')[0] if '_' in code_segment else code_segment

                    # 생성된 category_map에서 코드를 찾아 카테고리 이름 반환
                    return category_map.get(code, f"알 수 없는 카테고리 코드: {code}")

        except Exception as e:
            print(f"URL [{url}] 카테고리 분석 중 오류 발생: {e}")

        # 일치하는 패턴을 찾지 못하거나 오류 발생 시
        return "카테고리 분류 실패 (URL 패턴 불일치)"

    def get_ytn_article_data(url, headers, category_map):
        """
        단일 YTN 기사 URL에서 제목, 본문, 카테고리를 추출하는 함수
        생성된 category_map을 인자로 받습니다.
        """
        news_title = "제목 추출 실패"
        news_body = "본문 추출 실패"
        news_category = "카테고리 추출 실패" # 초기 카테고리 상태

        print(f"Processing URL: {url}")

        try:
            # 1. 웹페이지 HTML 가져오기
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.text

            # --- 디버깅: 가져온 HTML을 파일로 저장 ---
            file_name_safe = re.sub(r'[^\w.-]', '_', urlparse(url).path.strip('/')).strip('_')
            if not file_name_safe: file_name_safe = urlparse(url).hostname or 'debug'
            debug_file_path = f"debug_ytn_html_{file_name_safe}.html"
            try:
                with open(debug_file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"디버깅: 가져온 HTML 내용을 '{debug_file_path}' 파일로 저장했습니다.")
            except Exception as file_error:
                print(f"디버깅: HTML 파일 저장 중 오류 발생: {file_error}")
            # --- 디버깅 끝 ---

            # 2. BeautifulSoup으로 파싱
            soup = BeautifulSoup(html_content, 'html.parser')

            # --- 뉴스 제목 추출 (제공해주신 YTN 구조 반영) ---
            # h2 태그에 class 'news_title'를 찾고, 그 안의 span 텍스트를 가져옵니다.
            title_element_h2 = soup.find('h2', class_='news_title')

            if title_element_h2:
                title_element_span = title_element_h2.find('span')
                if title_element_span:
                    news_title = title_element_span.get_text(strip=True)
                    print(f"URL {url}: 제목 요소 (h2.news_title > span) 추출 성공.")
                else:
                    news_title = title_element_h2.get_text(strip=True) if title_element_h2.get_text(strip=True) else news_title
                    print(f"URL {url}: <h2 class='news_title'> 태그를 찾았으나 <span>이 없어 <h2> 텍스트 추출 시도.")
            else:
                print(f"URL {url}: 제목 요소를 찾지 못했습니다. (예상 선택자: h2.news_title)")


            # --- 뉴스 본문 추출 (제공해주신 div#CmAdContent.paragraph 구조 반영) ---
            # 본문 전체를 감싸는 div 요소를 찾습니다. id가 'CmAdContent'이고 class가 'paragraph'입니다.
            body_container = soup.find('div', id='CmAdContent', class_='paragraph')
            
            news_body = "본문 추출 실패"

            if body_container:
                # 불필요한 요소 (예: iframe 광고, 이미지 등) 제거
                for unnecessary_tag in body_container.find_all(['iframe', 'figure']):
                    unnecessary_tag.extract()

                news_body_raw = body_container.get_text(separator='\n', strip=True)

                # 불필요한 내용 제거 및 정리 (YTN 기사 하단부 패턴 제거)
                cleaned_body = news_body_raw
                cleaned_body = re.sub(r'YTN\s*[^(\n)]+\s*\([^@]+\@[^)]+\)\s*\n*', '', cleaned_body, flags=re.MULTILINE)
                cleaned_body = re.sub(r'※\s*.*?\[메일\].*?\n*', '', cleaned_body, flags=re.DOTALL)
                cleaned_body = re.sub(r'\[저작권자\(c\).+?\]\n*', '', cleaned_body)

                news_body = re.sub(r'\n\s*\n', '\n\n', cleaned_body).strip()

                if news_body:
                    print(f"URL {url}: 본문 요소 (div#CmAdContent.paragraph) 추출 성공.")
                else:
                    print(f"URL {url}: 본문 컨테이너는 찾았으나, 유효한 텍스트 내용이 없습니다 (정리 후 빈 내용).")
                    news_body = "본문 내용 없음"

            else:
                print(f"URL {url}: 본문 전체 컨테이너 요소를 찾지 못했습니다. (예상 선택자: div#CmAdContent.paragraph)")

            # --- 뉴스 카테고리 추출 (URL 경로 분석 - 생성된 맵 사용) ---
            # 생성된 ytn_category_map을 classify_ytn_category_from_url 함수에 전달
            news_category = classify_ytn_category_from_url(url, category_map)
            if news_category == "카테고리 분류 실패 (URL 패턴 불일치)" or news_category.startswith("알 수 없는 카테고리 코드"):
                print(f"URL {url}: URL 구조 분석으로 카테고리 추출/분류 실패: {news_category}")
            else:
                print(f"URL {url}: URL 구조 분석으로 카테고리 '{news_category}' 추출 성공.")

        except requests.exceptions.RequestException as e:
            print(f"URL {url}: 웹페이지를 가져오는 중 오류 발생: {e}")
            # 요청 실패 시 제목, 본문, 카테고리는 초기 실패 값 유지

        except Exception as e:
            print(f"URL {url}: 데이터 처리 중 예외 발생: {e}")
            # 데이터 처리 중 오류 발생 시 해당 값들은 초기 실패 값 유지
            if news_category == "카테고리 추출 실패": # 오류 발생했더라도 카테고리라도 추출 시도
                news_category = classify_ytn_category_from_url(url, category_map) # 맵을 전달

        # 최종 추출 결과 반환
        return {
            'URL': url,
            '제목': news_title,
            '본문': news_body,
            '카테고리': news_category
        }
    # User-Agent 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # 추출된 데이터를 저장할 리스트
    extracted_data_list = []

    # 각 URL에 대해 크롤링 및 데이터 추출 반복
    article_data = get_ytn_article_data(url, headers, ytn_category_map)
    extracted_data_list.append(article_data)

    print("\n모든 URL 처리 완료.")
    # --- 추출된 데이터를 Pandas DataFrame으로 변환 ---
    df_news = pd.DataFrame(extracted_data_list)
    from transformers import BertModel, BertTokenizer
    import torch
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    import nltk

    # 문장 분리
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize

    # 모델과 토크나이저 로드
    tokenizer = BertTokenizer.from_pretrained('monologg/kobert')
    model = BertModel.from_pretrained('monologg/kobert')
    model.eval()

    def get_sentence_embedding(sentence):
        inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            # [CLS] 토큰의 벡터 사용
            return outputs.last_hidden_state[:, 0, :].squeeze().numpy()

    import kss  # 한국어 문장 분리기

    def summarize(text, top_n=3):
        sentences = kss.split_sentences(text)
        embeddings = [get_sentence_embedding(sent) for sent in sentences]
        embeddings = np.array(embeddings)

        sim_matrix = cosine_similarity(embeddings, embeddings)
        scores = sim_matrix.sum(axis=1)

        ranked_sentences = [sent for _, sent in sorted(zip(scores, sentences), reverse=True)]
        return ranked_sentences[:top_n]


    # 예시 사용
    text = df_news['본문'].to_list()[0]
    summary = summarize(text)
    summary = " ".join(summary)
    return f"{summary}"
    print(summary)