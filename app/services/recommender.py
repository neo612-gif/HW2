"""
추천 서비스 로직 - 특징 기반 의상 조합 매칭
"""
import random
import logging
from typing import List

from app.schemas import OutfitCombination, OutfitItem, Season, Style, AnalysisResult
from app.services.image_analyzer import ImageAnalyzer
from app.model import OutfitModel

logger = logging.getLogger(__name__)

# 임의의 옷 아이템 DB (실제 서비스에서는 DB 연동)
MOCK_CLOTHES_DB = {
    "top": [
        {"name": "기본 화이트 티셔츠", "color": "화이트", "style": "casual", "score": 0.9},
        {"name": "오버핏 블랙 맨투맨", "color": "블랙", "style": "casual", "score": 0.8},
        {"name": "스카이블루 옥스퍼드 셔츠", "color": "블루", "style": "formal", "score": 0.85},
        {"name": "스트라이프 니트", "color": "네이비", "style": "classic", "score": 0.75},
        {"name": "그래픽 반팔티", "color": "블랙", "style": "street", "score": 0.8},
    ],
    "bottom": [
        {"name": "슬림핏 생지 데님", "color": "네이비", "style": "casual", "score": 0.9},
        {"name": "와이드 블랙 슬랙스", "color": "블랙", "style": "formal", "score": 0.85},
        {"name": "베이지 치노 팬츠", "color": "베이지", "style": "classic", "score": 0.8},
        {"name": "그레이 스웨트 팬츠", "color": "그레이", "style": "sporty", "score": 0.75},
        {"name": "카고 팬츠", "color": "카키", "style": "street", "score": 0.8},
    ]
}


class RecommenderService:
    def __init__(self, analyzer: ImageAnalyzer, model: OutfitModel):
        self.analyzer = analyzer
        self.model = model

    def get_recommendations(
        self,
        analysis: AnalysisResult,
        image_features: dict,
        season: Season = Season.all,
        target_style: Style = Style.casual,
        top_k: int = 3
    ) -> List[OutfitCombination]:
        """
        분석 결과를 바탕으로 최적의 옷 조합 추천
        """
        logger.info(f"추천 시작 (시즌: {season}, 타겟 스타일: {target_style})")
        
        recommendations = []
        body_type = analysis.detected_body_type
        
        # 실제로는 image_features["embedding"] 과 옷 벡터 간 Cosine Similarity를 계산하지만,
        # 여기서는 Mock DB와 룰 베이스 조합으로 가벼운 로직 구성
        
        # 1. 스타일에 맞는 아이템 필터링
        available_tops = [t for t in MOCK_CLOTHES_DB["top"] if t["style"] == target_style.value or target_style == Style.casual]
        available_bottoms = [b for b in MOCK_CLOTHES_DB["bottom"] if b["style"] == target_style.value or target_style == Style.casual]
        
        if not available_tops:
            available_tops = MOCK_CLOTHES_DB["top"]
        if not available_bottoms:
            available_bottoms = MOCK_CLOTHES_DB["bottom"]
            
        # 조합 생성
        for i in range(top_k):
            top_candidate = random.choice(available_tops)
            bottom_candidate = random.choice(available_bottoms)
            
            # 체형에 따른 추천 이유 생성
            reason = self._generate_reason(body_type, top_candidate, bottom_candidate)
            
            top_item = OutfitItem(
                category="top",
                name=top_candidate["name"],
                color=top_candidate["color"],
                style=top_candidate["style"],
                description=f"{target_style.value} 스타일에 어울리는 상의",
                confidence=round(random.uniform(0.7, 0.95), 2)
            )
            
            bottom_item = OutfitItem(
                category="bottom",
                name=bottom_candidate["name"],
                color=bottom_candidate["color"],
                style=bottom_candidate["style"],
                description=f"{target_style.value} 스타일에 어울리는 하의",
                confidence=round(random.uniform(0.7, 0.95), 2)
            )
            
            overall_score = (top_item.confidence + bottom_item.confidence) / 2.0
            
            comb = OutfitCombination(
                top=top_item,
                bottom=bottom_item,
                overall_score=round(overall_score, 2),
                style_theme=target_style.value,
                occasion="외출/데이트" if target_style == Style.casual else "출근/격식있는 자리",
                reason=reason
            )
            recommendations.append(comb)
            
        # 점수 순 정렬
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        return recommendations
        
    def _generate_reason(self, body_type: str, top: dict, bottom: dict) -> str:
        if body_type == "슬림형":
            return f"슬림한 체형을 보완해주는 {top['color']} 상의와 자연스러운 실루엣의 {bottom['color']} 하의 조합입니다."
        elif body_type == "표준형":
            return f"표준 체형에 무난하게 어울리는 안정적인 조합입니다."
        else:
            return f"전체적인 비율을 잡아주는 조합으로, {top['color']} 색상이 상의 포인트를 줍니다."
