from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    DEEPSEEK_API_KEY: str
    RUNPOD_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # DeepSeek
    DEEPSEEK_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET_KEY: str = "jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # Task Settings
    MAX_ITERATIONS: int = 10
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3600
    CELERY_TASK_TIME_LIMIT: int = 3900
    CELERY_BROKER_CONNECTION_MAX_RETRIES: int = 10
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()