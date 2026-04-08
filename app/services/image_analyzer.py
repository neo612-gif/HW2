"""
이미지 분석 서비스 - 업로드된 전신 이미지를 분석하여 특징 추출
"""
import logging
import io
from typing import List
from PIL import Image

from app.model import OutfitModel
from app.schemas import AnalysisResult

logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """업로드 이미지 전처리 및 분석 서비스"""

    def __init__(self, model: OutfitModel):
        self.model = model

    def preprocess(self, image_bytes: bytes) -> Image.Image:
        """
        업로드된 바이트 데이터를 PIL 이미지로 변환 및 전처리
        - 최대 크기 제한 (1024x2048)
        - RGB 변환 (RGBA, grayscale 대응)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"이미지를 열 수 없습니다: {e}")

        # RGBA → RGB 변환 (투명도 채널 제거)
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 해상도 제한 (비율 유지)
        max_w, max_h = 1024, 2048
        image.thumbnail((max_w, max_h), Image.LANCZOS)

        return image

    def analyze(self, image: Image.Image) -> AnalysisResult:
        """
        이미지에서 피부 톤, 체형, 주요 색상 추출
        """
        logger.info("이미지 분석 시작")

        skin_tone = self.model.analyze_skin_tone(image)
        body_type = self.model.analyze_body_type(image)
        dominant_colors = self.model.get_dominant_colors(image, n_colors=5)

        logger.info(
            f"분석 완료 - 피부 톤: {skin_tone}, 체형: {body_type}, "
            f"주요 색상: {dominant_colors}"
        )

        return AnalysisResult(
            detected_skin_tone=skin_tone,
            detected_body_type=body_type,
            detected_current_outfit=None,  # 향후 세그멘테이션 모델로 확장 가능
            dominant_colors=dominant_colors,
        )

    def get_image_features(self, image: Image.Image) -> dict:
        """
        CLIP 임베딩 + 분류 결과를 통합하여 반환
        """
        from app.model import TOP_PROMPTS, BOTTOM_PROMPTS

        embedding = self.model.get_image_embedding(image)
        top_scores = self.model.classify_with_prompts(image, TOP_PROMPTS)
        bottom_scores = self.model.classify_with_prompts(image, BOTTOM_PROMPTS)

        return {
            "embedding": embedding,
            "top_scores": sorted(top_scores, key=lambda x: x[1], reverse=True),
            "bottom_scores": sorted(bottom_scores, key=lambda x: x[1], reverse=True),
        }
