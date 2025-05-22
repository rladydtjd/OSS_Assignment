from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd # pandas 라이브러리 임포트

# Flask 앱 인스턴스 생성
app = Flask(__name__)

# CSV 파일 경로 (main.py 파일과 같은 폴더에 있다고 가정합니다)
# 파일 이름을 '띠별_년생_운세수정버전.csv'로 수정했습니다.
CSV_FILE_PATH = '띠별_년생_운세수정버전.csv'
# 운세 데이터를 저장할 DataFrame 변수
fortune_df = None

# Flask 앱이 시작될 때 CSV 파일을 로드합니다.
def load_fortune_data():
    
    global fortune_df
    try:
        # CSV 파일을 DataFrame으로 읽어옵니다.
        # header=None: CSV 파일에 헤더가 없음을 명시
        # encoding='utf-8-sig': 한글 깨짐 방지를 위해 사용
        # sep=',': 쉼표로 구분된 파일임을 명시 (보통 기본값이지만 명시적으로 작성)
        fortune_df = pd.read_csv(CSV_FILE_PATH, encoding='euc-kr', sep=',', header=None, dtype={1: int})
        # 컬럼에 알기 쉬운 이름 지정 (데이터 형식: 띠, 년도, 운세내용)
        fortune_df.columns = ['띠', '년도', '운세내용']
        print("\n--- DataFrame 정보 ---") # 추가
        print(fortune_df.info())       # 추가: 컬럼 타입 확인
        print("\n--- DataFrame 첫 5행 ---") # 추가
        print(fortune_df.head())       # 추가: 실제 데이터 값 확인
        print("---------------------\n") # 추가
        print(f"'{CSV_FILE_PATH}' 파일 로드 성공.")
        # 로드된 데이터프레임 확인 (선택 사항)
        # print(fortune_df.head())
    except FileNotFoundError:
        print(f"!!! 오류: '{CSV_FILE_PATH}' 파일을 찾을 수 없습니다. 크롤링 코드를 먼저 실행하여 파일을 생성해주세요.")
        fortune_df = pd.DataFrame() # 파일이 없으면 빈 DataFrame 생성
    except Exception as e:
        print(f"!!! 오류: CSV 파일 로드 중 오류 발생: {e}")
        fortune_df = pd.DataFrame()

# 앱 컨텍스트가 푸시될 때 데이터 로드 (최신 Flask 버전 권장 방식)
with app.app_context():
    load_fortune_data()

# 루트 경로 - 메인 페이지 렌더링
@app.route('/')
def index():
    # HTML 파일 이름이 다르다면 'index.html' 대신 해당 파일 이름을 사용하세요.
    return render_template('index.html')

# 뉴스 요약 API 엔드포인트 (이전 코드와 동일)
@app.route('/api/summarize', methods=['POST'])
def summarize_news():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL을 입력해주세요.'}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        summary = text[:500] + "..." if len(text) > 500 else text

        return jsonify({'summary': summary})

    except requests.exceptions.RequestException as e:
        print(f"URL 요청 중 오류 발생: {e}")
        return jsonify({'error': '뉴스 내용을 가져오지 못했습니다.'}), 500
    except Exception as e:
        print(f"뉴스 요약 중 오류 발생: {e}")
        return jsonify({'error': '뉴스 요약 중 오류가 발생했습니다.'}), 500

# 실시간 인기 뉴스 API 엔드포인트 (이전 코드와 동일)
@app.route('/api/trending-news', methods=['GET'])
def get_trending_news():
    top_n = request.args.get('top_n', 5, type=int)
    trending_data = [
        {'title': '오늘의 주요 경제 지표 발표', 'url': '#'},
        {'title': 'AI 기술, 산업 전반에 영향', 'url': '#'},
        {'title': '최신 스마트폰 출시 소식', 'url': '#'},
        {'title': '주말 날씨 예보', 'url': '#'},
        {'title': '건강한 식습관 팁', 'url': '#'},
    ]
    return jsonify({'trending': trending_data[:top_n]})

# 운세 검색 API 엔드포인트
@app.route('/api/fortune', methods=['POST'])
def get_fortune():
    # 웹페이지에서 전송된 출생 연도를 받습니다.
    data = request.get_json()
    birth_year = data.get('birth_year') # 프론트에서 숫자로 보내므로 int 형변환 시도

    if birth_year is None: # birth_year가 None일 경우 처리
         return jsonify({'error': '출생 연도를 입력해주세요.'}), 400

    # 입력받은 년도가 유효한 숫자인지 확인
    try:
        birth_year_int = int(birth_year)
    except (ValueError, TypeError): # int 형변환 실패 시 오류
        return jsonify({'error': '유효하지 않은 출생 연도 형식입니다. 숫자를 입력해주세요.'}), 400

    # DataFrame이 로드되지 않았거나 비어있으면 오류 반환
    if fortune_df is None or fortune_df.empty:
        return jsonify({'error': '운세 데이터를 불러올 수 없습니다. CSV 파일을 확인해주세요.'}), 500

    # DataFrame에서 입력된 년도와 정확히 일치하는 행을 찾습니다.
    # CSV 파일의 '년도' 컬럼은 정수형으로 로드되었다고 가정합니다.
    try:
        # 컬럼 이름 '년도'를 사용하여 검색
        found_fortunes = fortune_df[fortune_df['년도'] == birth_year_int]
    except KeyError:
        # load_fortune_data에서 컬럼 이름 지정이 실패했거나 잘못된 경우
         return jsonify({'error': "데이터 처리 오류: '년도' 컬럼을 찾을 수 없습니다."}), 500

    # 검색된 결과가 있는지 확인
    if not found_fortunes.empty:
        # 첫 번째로 찾은 결과 사용
        try:
            # 컬럼 이름 '띠'와 '운세내용'을 사용하여 데이터 가져오기
            띠 = found_fortunes.iloc[0]['띠']
            운세 = found_fortunes.iloc[0]['운세내용'] # 컬럼 이름 '운세내용' 사용
            # 프론트엔드에서 '운세' 키를 기대하므로, '운세내용' 값을 '운세' 키로 반환
            return jsonify({'띠': 띠, '운세': 운세}), 200
        except KeyError as e:
             # '띠' 또는 '운세내용' 컬럼이 없는 경우
             return jsonify({'error': f"데이터 형식 오류: 필요한 컬럼({e})이 CSV 파일에 없습니다."}), 500
        except IndexError:
             # 데이터는 찾았지만 행이 비어있는 이상한 경우 (발생 가능성 낮음)
             return jsonify({'error': "운세 데이터를 가져오는 중 예상치 못한 오류가 발생했습니다."}), 500

    else:
        # 해당 년생의 운세가 없는 경우
        return jsonify({'error': f'{birth_year_int}년생의 운세 데이터를 찾을 수 없습니다.'}), 404

# Flask 앱 실행
if __name__ == '__main__':
    # debug=True로 설정하면 코드 변경 시 서버가 자동으로 재시작됩니다. 개발 시 유용합니다.
    app.run(debug=True)
