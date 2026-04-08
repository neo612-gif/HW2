import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.endpoints import router as recommend_router
from app.schemas import HealthResponse
from app.model import get_model

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작 및 종료 라이프사이클 관리
    """
    # 서버 기동 시 머신러닝 모델을 백그라운드에서 로드하여
    # 첫 요청의 지연 시간을 최소화합니다.
    logger.info("Initializing ML Model...")
    ml_model = get_model()
    try:
        # 모델을 미리 로드하지 않으면 첫 API 호출 시 로딩됨 (메모리 관리 목적이라면 주석 처리 가능)
        ml_model.load()
        logger.info("ML Model Loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load ML model on startup: {str(e)}")
        
    yield
    
    # 서버 종료 시 리소스 정리
    logger.info("Shutting down Application...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="경량 이미지 분류 모델을 사용한 옷 조합 추천 API 서버",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS 설정 (React, Vue 등 프론트엔드 연동을 위함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스 시 특정 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(recommend_router)

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """서버 및 모델 상태를 반환합니다."""
    model = get_model()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        model_loaded=model.is_loaded
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
