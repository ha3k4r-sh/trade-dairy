import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./trade_diary.db"
    SECRET_KEY: str = "change-this-secret-key-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Default user credentials
    DEFAULT_USERNAME: str = "admin"
    DEFAULT_PASSWORD: str = "admin"
    
    class Config:
        env_file = ".env"

settings = Settings()
