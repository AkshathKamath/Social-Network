# app/models/follow.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FollowResponse(BaseModel):
    message: str
    following: bool

class FollowersResponse(BaseModel):
    followers: List[dict]
    count: int

class FollowingResponse(BaseModel):
    following: List[dict]
    count: int

class RelationshipResponse(BaseModel):
    following: bool
    followed_by: bool