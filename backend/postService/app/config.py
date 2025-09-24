# app/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Explicitly load .env file BEFORE creating Settings
load_dotenv()

class Settings(BaseSettings):
    ## app
    app_name: str = "Post Service"
    debug: bool = True

    # supabase
    supabase_url: str
    supabase_service_key: str

    ## redis
    redis_url: str

    ## mongo
    mongo_url: str

    ## jwt
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create instance
settings = Settings()