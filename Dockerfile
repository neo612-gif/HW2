# 1. 파이썬 3.11 슬림 이미지 사용 (경량화)
FROM python:3.11-slim

# 2. 작업 시스템 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정
# 로그가 버퍼링 없이 즉시 출력되도록 설정
ENV PYTHONUNBUFFERED=1
# HuggingFace 모델이 다운로드 될 경로를 이미지 내부 캐시로 지정
ENV HF_HOME=/app/.cache/huggingface
# FastAPI 구동 설정
ENV HOST=0.0.0.0
ENV PORT=8000

# 4. 필수 시스템 패키지 설치 및 찌꺼기 제거 (캐시 최적화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. 파이썬 패키지 설치
# 패키지 명세서 먼저 복사 (소스코드 변경시 패키지 재설치 방지 - 캐시 레이어 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. ML 모델 사전 다운로드 (핵심 최적화 부분)
# 도커 이미지를 구울 때(Build) 모델을 미리 다운받습니다.
# 이후 도커를 실행(Run)할 때는 모델 다운로드를 기다리지 않고 1초 만에 서버가 켜집니다.
RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
print('Downloading CLIP weights...'); \
CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); \
CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); \
print('Download Complete!')"

# 7. 전체 소스코드 복사
COPY app/ ./app/

# 8. 컨테이너 개방 포트
EXPOSE 8000

# 9. 서버 실행 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
