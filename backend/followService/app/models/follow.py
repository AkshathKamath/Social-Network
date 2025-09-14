# app/models/follow.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    user_name: Optional[str] = None

class FollowResponse(BaseModel):
    message: str
    following: bool

class FollowersResponse(BaseModel):
    followers: List[User]

class FollowingResponse(BaseModel):
    following: List[User]

# class RelationshipResponse(BaseModel):
#     following: bool
#     followed_by: bool