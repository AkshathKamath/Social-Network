# app/models/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from uuid import UUID
from .token import Token

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    user_name: str = Field(..., min_length=3, max_length=50)
    date_of_birth: date

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    user_name: Optional[str] = None

class User(BaseModel):
    token: Optional[Token] = None
    user_id: str
    full_name: str
    user_name: str
    image_url: Optional[str] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0

class Image(BaseModel):
    image_data: bytes
    file_name: str

class Message(BaseModel):
    message: str