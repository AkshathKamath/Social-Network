from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Following(BaseModel):
    user_id: str

class Post(BaseModel):
    post_id: str
    user_id: str
    post_url: str
    caption: Optional[str] = None
    created_at: datetime