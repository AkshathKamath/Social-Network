# app/models/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from uuid import UUID

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    user_name: str
    date_of_birth: date

class UserLogin(BaseModel):
    email: EmailStr
    password: str