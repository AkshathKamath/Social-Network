from app.models.feed import Post
from app.services.feed_service import feed_service_obj
from app.core.dependencies import get_current_user
from fastapi import APIRouter, Depends
from typing import List, Dict


router = APIRouter(prefix="/feed", tags=["Feed"])

@router.get("/view_feed", response_model=List[Post])
async def view_feed(current_user: Dict = Depends(get_current_user)):
    return feed_service_obj.generate_feed(user_id=current_user['user_id'])
