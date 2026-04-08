"""
설정 파일 - 환경 변수 및 앱 설정 관리
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Outfit Recommender API"
    app_version: str = "1.0.0"
    debug: bool = False

    # 업로드 설정
    max_upload_size_mb: int = 10
    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]

    # 모델 설정
    model_name: str = "openai/clip-vit-base-patch32"
    top_k_recommendations: int = 5

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
