from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PostData(BaseModel):
    image_data: bytes
    file_extension: str
    caption: Optional[str] = None

class Post(BaseModel):
    user_id: str
    post_url: str
    caption: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PostUploadResponse(BaseModel):
    post_id: str
    message: str

class PostFetchResponse(BaseModel):
    post_id: str
    user_id: str
    post_url: str
    caption: Optional[str] = None
    created_at: datetime

class PostDeleteResponse(BaseModel):
    message: str