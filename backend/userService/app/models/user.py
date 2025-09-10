# app/models/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from uuid import UUID

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    user_name: str = Field(..., min_length=3, max_length=50)
    date_of_birth: date

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    email: EmailStr
    full_name: str
    user_name: str