"""
스키마 정의 - 요청/응답 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Season(str, Enum):
    spring = "spring"
    summer = "summer"
    fall = "fall"
    winter = "winter"
    all = "all"


class Style(str, Enum):
    casual = "casual"
    formal = "formal"
    sporty = "sporty"
    street = "street"
    classic = "classic"


class OutfitItem(BaseModel):
    category: str = Field(..., description="카테고리 (top/bottom)")
    name: str = Field(..., description="아이템 이름")
    color: str = Field(..., description="색상")
    style: str = Field(..., description="스타일")
    description: str = Field(..., description="설명")
    confidence: float = Field(..., ge=0.0, le=1.0, description="추천 신뢰도")


class OutfitCombination(BaseModel):
    top: OutfitItem = Field(..., description="상의")
    bottom: OutfitItem = Field(..., description="하의")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="전체 조합 점수")
    style_theme: str = Field(..., description="스타일 테마")
    occasion: str = Field(..., description="착용 상황")
    reason: str = Field(..., description="추천 이유")


class AnalysisResult(BaseModel):
    detected_skin_tone: str = Field(..., description="감지된 피부 톤")
    detected_body_type: str = Field(..., description="감지된 체형")
    detected_current_outfit: Optional[str] = Field(None, description="현재 착용 중인 옷")
    dominant_colors: List[str] = Field(..., description="이미지의 주요 색상들")


class RecommendationResponse(BaseModel):
    status: str = Field(default="success")
    analysis: AnalysisResult = Field(..., description="이미지 분석 결과")
    recommendations: List[OutfitCombination] = Field(..., description="추천 조합 리스트")
    season: str = Field(..., description="추천 시즌")
    style: str = Field(..., description="추천 스타일")
    message: str = Field(default="추천이 성공적으로 생성되었습니다.")


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field(default="healthy")
    version: str
    model_loaded: bool
