from app.models.post import PostData, Post, PostUploadResponse, PostFetchResponse, PostDeleteResponse
from app.services.post_service import PostService, get_post_service
from app.core.dependencies import get_current_user

from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Dict
import json
import logging



logger = logging.getLogger(__name__)
router = APIRouter(prefix="/post", tags=["Posts"])

@router.post("/upload_post", response_model=PostUploadResponse)
async def upload_post(
    file: UploadFile = File(...), 
    data: str = Form(...),
    current_user: Dict = Depends(get_current_user),
    post_service_obj: PostService = Depends(get_post_service) ## Dependency injection so that every request gets its own post service object and we do not share state btw requests
    ):
    file_data = await file.read()
    file_extension = file.filename.split('.')[-1]
    json_data = json.loads(data)
    caption = json_data.get("caption", "")
    user_id = current_user['user_id']
    result = await post_service_obj.upload_post(PostData(image_data=file_data, file_extension=file_extension, caption=caption), user_id=user_id)
    logger.info(f"Post {result.post_id} uploaded successfully")
    return result

@router.get("/get_post/{user_id}", response_model=list[PostFetchResponse])
async def get_post(
    user_id: str,
    post_service_obj: PostService = Depends(get_post_service)
):
    return await post_service_obj.get_post(user_id=user_id)

@router.delete("/delete_post/{post_id}", response_model=PostDeleteResponse)
async def delete_post(
    post_id: str, 
    current_user: Dict = Depends(get_current_user),
    post_service_obj: PostService = Depends(get_post_service)
    ):
    return post_service_obj.delete_post(post_id=post_id, user_id=current_user['user_id'])