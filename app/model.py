"""
ML 모델 서비스 - CLIP 모델을 활용한 이미지 임베딩 및 색상 분석
경량 모델(CLIP ViT-B/32)을 사용하여 이미지 특징 추출
"""
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)

# 옷 카테고리 프롬프트 (CLIP zero-shot 분류용)
TOP_PROMPTS = [
    "a white casual t-shirt",
    "a black formal dress shirt",
    "a blue denim jacket",
    "a striped polo shirt",
    "a grey hoodie sweatshirt",
    "a floral blouse",
    "a navy blue blazer",
    "a beige knit sweater",
    "a red graphic tee",
    "a cream linen shirt",
]

BOTTOM_PROMPTS = [
    "dark blue slim jeans",
    "black dress trousers",
    "khaki chino pants",
    "grey sweatpants",
    "white midi skirt",
    "floral summer skirt",
    "black leather mini skirt",
    "beige wide leg pants",
    "navy shorts",
    "olive cargo pants",
]

STYLE_THEMES = {
    "casual": ["casual t-shirt", "hoodie", "jeans", "sneakers"],
    "formal": ["dress shirt", "blazer", "trousers", "leather shoes"],
    "sporty": ["polo shirt", "sweatpants", "shorts", "athletic wear"],
    "street": ["graphic tee", "cargo pants", "denim jacket", "streetwear"],
    "classic": ["knit sweater", "chino pants", "linen shirt", "classic style"],
    "minimal": ["minimalist shirt", "plain trousers", "clean minimal look"],
    "dandy": ["neat cardigan", "slacks", "loafers", "sophisticated look"],
    "gorpcore": ["technical windbreaker", "cargo pants", "technical jacket", "outdoor gear"],
    "preppy": ["polo shirt", "v-neck sweater", "chino shorts", "academic style"],
}

OCCASIONS = {
    0: "데일리 캐주얼",
    1: "비즈니스 캐주얼",
    2: "야외 활동",
    3: "스트리트 패션",
    4: "클래식 룩",
}


class OutfitModel:
    """CLIP 기반 경량 패션 추천 모델"""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._is_loaded = False

    def load(self):
        """모델 로드 (최초 1회, 이후 캐시 사용)"""
        if self._is_loaded:
            return

        logger.info(f"CLIP 모델 로딩 중: {self.model_name} (device: {self.device})")
        try:
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
            logger.info("✅ CLIP 모델 로드 완료")
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {e}")
            raise

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def get_image_embedding(self, image: Image.Image) -> np.ndarray:
        """이미지를 CLIP 임베딩으로 변환"""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            embedding = self.model.get_image_features(**inputs)
            # 모델 버전에 따라 객체가 반환될 경우를 대비해 텐서만 추출
            if not hasattr(embedding, "cpu"):
                embedding = getattr(embedding, "pooler_output", embedding[0])
        return embedding.cpu().numpy().flatten()

    def classify_with_prompts(
        self, image: Image.Image, prompts: List[str]
    ) -> List[Tuple[str, float]]:
        """Zero-shot 분류: 이미지 vs 텍스트 프롬프트 유사도 계산"""
        inputs = self.processor(
            text=prompts,
            images=image,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits_per_image  # shape: (1, len(prompts))
            probs = logits.softmax(dim=-1).cpu().numpy().flatten()

        return list(zip(prompts, probs.tolist()))

    def get_dominant_colors(self, image: Image.Image, n_colors: int = 5) -> List[str]:
        """K-means 없이 PIL 양자화로 주요 색상 추출 (경량 처리)"""
        img_resized = image.convert("RGB").resize((150, 150))
        quantized = img_resized.quantize(colors=n_colors, method=Image.Quantize.FASTOCTREE)
        palette = quantized.getpalette()

        colors = []
        for i in range(n_colors):
            r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
            colors.append(self._rgb_to_color_name(r, g, b))

        return list(dict.fromkeys(colors))  # 중복 제거, 순서 유지

    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """RGB 값을 한글 색상 이름으로 변환"""
        color_map = {
            "블랙": (0, 0, 0),
            "화이트": (255, 255, 255),
            "그레이": (128, 128, 128),
            "네이비": (0, 0, 128),
            "블루": (0, 0, 255),
            "베이지": (245, 245, 220),
            "브라운": (165, 42, 42),
            "레드": (255, 0, 0),
            "그린": (0, 128, 0),
            "올리브": (128, 128, 0),
            "카키": (189, 183, 107),
            "크림": (255, 253, 208),
        }
        min_dist = float("inf")
        closest = "그레이"
        for name, (cr, cg, cb) in color_map.items():
            dist = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = name
        return closest

    def analyze_body_type(self, image: Image.Image) -> str:
        """이미지 비율로 간소화된 체형 추정"""
        w, h = image.size
        ratio = h / w if w > 0 else 1.0
        if ratio > 2.2:
            return "슬림형"
        elif ratio > 1.8:
            return "표준형"
        else:
            return "균형형"

    def analyze_skin_tone(self, image: Image.Image) -> str:
        """이미지 상단 영역 평균 색상으로 피부 톤 추정"""
        img_rgb = image.convert("RGB").resize((100, 200))
        # 상반신 중앙 영역
        region = img_rgb.crop((30, 20, 70, 80))
        pixels = list(region.getdata())
        avg_r = sum(p[0] for p in pixels) / len(pixels)
        avg_g = sum(p[1] for p in pixels) / len(pixels)

        if avg_r > 200:
            return "밝은 피부"
        elif avg_r > 160:
            return "중간 피부"
        else:
            return "어두운 피부"


# 싱글턴 인스턴스
_model_instance: OutfitModel = None


def get_model() -> OutfitModel:
    """싱글턴 모델 인스턴스 반환"""
    global _model_instance
    if _model_instance is None:
        _model_instance = OutfitModel()
    return _model_instance
