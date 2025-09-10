from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data stored in token"""
    user_id: str
    user_name: str

class RefreshToken(BaseModel):
    refresh_token: str

class LogoutMessage(BaseModel):
    message: str