"""Configuration management for the Fall Detection System."""

from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class TelegramConfig(BaseSettings):
    """Telegram bot configuration."""

    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    @field_validator("bot_token")
    def validate_bot_token(cls, v):
        if not v:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        return v

    class Config:
        env_prefix = "TELEGRAM_"


class ModelConfig(BaseSettings):
    """Model and AI configuration."""

    yolo_person_path: str = Field(default="models/yolo11s-final.pt")
    tracking_config_path: str = Field(default="models/botsort.yaml")
    device: str = Field(default="cpu")
    face_embedding_path: str = Field(default="face_emb/")
    fall_class_idx: int = Field(default=1)
    fall_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    face_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    face_id_threshold: float = Field(default=1.22, ge=0.0)
    threshold_fall_frames: int = Field(default=5, ge=1)
    max_identification_attempts: int = Field(default=5, ge=1)
    identification_timeout: float = Field(default=1.0, ge=0.1)

    @field_validator("yolo_person_path")
    def validate_yolo_path(cls, v):
        if not Path(v).exists():
            raise ValueError(f"YOLO model path does not exist: {v}")
        return v

    class Config:
        env_prefix = "MODEL_"


class VideoConfig(BaseSettings):
    """Video processing configuration."""

    source: str = Field(default="1")
    display_width: int = Field(default=800, gt=0)
    frame_rate_divisor: int = Field(default=10, gt=0)
    stream_sleep_interval: float = Field(default=0.5, ge=0.1)

    @field_validator("source")
    def validate_video_source(cls, v):
        # Check if it's a file path or camera index
        if v.isdigit():
            return int(v)  # Camera index
        elif Path(v).exists():
            return str(v)  # File path
        else:
            raise ValueError(f"Video source does not exist: {v}")

    class Config:
        env_prefix = "VIDEO_"


class AppConfig(BaseSettings):
    """Flask application configuration."""

    debug: bool = Field(default=True)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=5000, gt=0, le=65535)
    secret_key: str = Field(default="secret")

    class Config:
        env_prefix = "APP_"


class Settings:
    """Main settings class that combines all configuration sections."""

    def __init__(self):
        self.telegram = TelegramConfig()
        self.model = ModelConfig()
        self.video = VideoConfig()
        self.app = AppConfig()

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary format."""
        return {
            "telegram": self.telegram.model_dump(),
            "model": self.model.model_dump(),
            "video": self.video.model_dump(),
            "app": self.app.model_dump(),
        }

    def get_tracker_config(self) -> Dict[str, Any]:
        """Get configuration specifically for FallAndFaceTracker."""
        return {
            "yolo_person_path": self.model.yolo_person_path,
            "video_source": self.video.source,
            "face_db": None,
            "fall_conf": self.model.fall_confidence,
            "face_conf": self.model.face_confidence,
            "face_id_threshold": self.model.face_id_threshold,
            "fall_class_idx": self.model.fall_class_idx,
            "threshold_fall_frames": self.model.threshold_fall_frames,
        }


settings = Settings()
