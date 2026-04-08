from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import ValidationError
import logging

from app.schemas import RecommendationResponse, ErrorResponse, Season, Style
from app.services.image_analyzer import ImageAnalyzer
from app.services.recommender import RecommenderService
from app.model import get_model
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recommend", tags=["Recommendations"])


@router.post("/", response_model=RecommendationResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_outfit_recommendation(
    image: UploadFile = File(..., description="전신 이미지 파일"),
    season: Season = Form(Season.all, description="추천 시즌 (기본: all)"),
    style: Style = Form(Style.casual, description="원하는 스타일 (기본: casual)"),
    settings: Settings = Depends(get_settings)
):
    """
    이미지를 업로드하고 체형, 피부톤 등을 분석하여 추천 옷 조합을 반환합니다.
    """
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식입니다. 지원 형식: {settings.allowed_image_types}")

    # 파일 크기 검증을 하려면 이미지 전체를 읽어야 하므로 아래에서 체크
    image_bytes = await image.read()
    if len(image_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.max_upload_size_mb}MB 이하여야 합니다.")

    try:
        # 서비스 객체 초기화 (의존성 주입 형태로도 개선 가능)
        ml_model = get_model()
        analyzer = ImageAnalyzer(model=ml_model)
        recommender = RecommenderService(analyzer=analyzer, model=ml_model)

        # 1. 이미지 전처리
        pil_image = analyzer.preprocess(image_bytes)
        
        # 2. 이미지 특징 및 속성 분석
        analysis_result = analyzer.analyze(pil_image)
        image_features = analyzer.get_image_features(pil_image)
        
        # 3. 옷 조합 추천
        recommendations = recommender.get_recommendations(
            analysis=analysis_result,
            image_features=image_features,
            season=season,
            target_style=style,
            top_k=settings.top_k_recommendations
        )
        
        return RecommendationResponse(
            analysis=analysis_result,
            recommendations=recommendations,
            season=season.value,
            style=style.value
        )
        
    except Exception as e:
        logger.error(f"추천 처리 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 내부에서 추천을 처리하는 중 오류가 발생했습니다.")
