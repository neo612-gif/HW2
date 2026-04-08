# Outfit Recommender API

FastAPI와 OpenAI의 CLIP 경량 모델(`ViT-B/32`)을 활용한 전신 이미지 기반 옷 추천 API 서버입니다. 
사용자의 사진을 분석해 체형, 피부톤, 옷 스타일 등을 파악하고 그에 맞는 상하의 조합을 추천합니다.

## 디렉토리 구조 (Directory Structure)

```text
outfit-recommender/
│
├── app/
│   ├── __init__.py          # 앱 패키지
│   ├── main.py              # FastAPI 진입점 (앱 실행 파일)
│   ├── config.py            # 환경 변수 및 공통 설정
│   ├── schemas.py           # Pydantic을 이용한 요청/응답 데이터 모델
│   ├── model.py             # CLIP 모델 초기화, 임베딩 및 추론 관련 함수
│   │
│   ├── api/                 # API 라우트
│   │   ├── __init__.py
│   │   └── endpoints.py     # 추천 비즈니스 로직에 연결되는 API 엔드포인트
│   │
│   └── services/            # 비즈니스 로직
│       ├── __init__.py
│       ├── image_analyzer.py # 전신 이미지 전처리, 색상 도출 및 특징 분석
│       └── recommender.py    # 분석 결과를 기반으로 어울리는 코디 조합
│
├── requirements.txt         # 파이썬 의존성 패키지 목록
└── README.md                # 프로젝트 설명 파일
```

## 실행 방법 (How to Run)

### 1. 파이썬 가상환경 생성 (권장)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 패키지 설치
GPU 환경(CUDA)이 준비되어 있는 경우 `PyTorch` 등은 `requirements.txt`에 명시된 대로 GPU 버전으로 받아집니다.
```bash
pip install -r requirements.txt
```

### 3. API 서버 실행
```bash
uvicorn app.main:app --reload
```
서버가 실행되면 다음 주소로 접속할 수 있습니다:
- **API 서버 주소**: http://127.0.0.1:8000
- **Swagger UI (API 문서)**: http://127.0.0.1:8000/docs
- **Redoc (API 문서 2)**: http://127.0.0.1:8000/redoc

### 4. API 테스트 방법
- `/docs` 에 접속합니다.
- `POST /api/v1/recommend/` 엔드포인트를 열고 `Try it out`을 클릭합니다.
- 본인의 전신 사진을 업로드하고 (image), season과 style을 선택한 후 `Execute`를 누르면 응답 결과를 확인할 수 있습니다.

## 배포 및 운영 팁 (MLOps 관점)
- 현재는 FastAPI 생명주기를 통해 서버 시작 시에 CLIP 모델을 메모리에 로드하도록 설정했습니다.
- 추후 Dockerfile을 추가하여 컨테이너 환경으로 배포하고, Celery 등과 연동하여 GPU 자원을 큐(Queue) 베이스로 관리하는 형태로 확장하는 것이 좋습니다.
