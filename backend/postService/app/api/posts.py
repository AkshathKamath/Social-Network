from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.models.post import PostData, Post, PostUploadResponse, PostFetchResponse, PostDeleteResponse
from app.services.post_service import post_obj
from app.core.dependencies import get_current_user
from typing import Dict
import json

router = APIRouter(prefix="/post", tags=["Posts"])

@router.post("/upload_post", response_model=PostUploadResponse)
async def upload_post(file: UploadFile = File(...), data: str = Form(...),current_user: Dict = Depends(get_current_user)):
    file_data = await file.read()
    file_extension = file.filename.split('.')[-1]
    json_data = json.loads(data)
    caption = json_data.get("caption", "")
    user_id = current_user['user_id']
    return post_obj.upload_post(PostData(image_data=file_data, file_extension=file_extension, caption=caption), user_id=user_id)

@router.get("/get_post/{user_id}", response_model=list[PostFetchResponse])
async def get_post(user_id: str):
    return post_obj.get_post(user_id=user_id)

@router.delete("/delete_post/{post_id}", response_model=PostDeleteResponse)
async def delete_post(post_id: str, current_user: Dict = Depends(get_current_user)):
    return post_obj.delete_post(post_id=post_id, user_id=current_user['user_id'])