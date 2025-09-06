# app/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Explicitly load .env file BEFORE creating Settings
load_dotenv()

class Settings(BaseSettings):
    app_name: str = "User Service"
    debug: bool = True
    supabase_url: str
    supabase_service_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create instance
settings = Settings()