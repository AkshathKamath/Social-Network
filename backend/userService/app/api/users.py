# app/api/users.py (new file)
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import User, Image, Message
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.user_service import user_obj
from typing import Dict

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current user's profile
    This endpoint is PROTECTED - requires valid JWT token
    """
    return user_obj.get_user(current_user['user_id'])

@router.put("/me", response_model=User)
async def update_my_profile(
    update_data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update current user's profile
    PROTECTED - requires valid JWT token
    """
    return user_obj.update_user(updated_user=update_data, user_id=current_user['user_id'])
    # if not result.data:
    #     raise HTTPException(status_code=404, detail="User not found")
    

@router.delete("/me", response_model=Message)
async def delete_my_account(current_user: Dict = Depends(get_current_user)):
    """
    Delete current user's account
    PROTECTED - requires valid JWT token
    """
    return user_obj.delete_user(user_id= current_user['user_id'])


@router.put("/profile_image", response_model=Message)
async def update_profile_image(file: UploadFile = File(...), current_user: Dict = Depends(get_current_user)):

    file_data = await file.read()
    file_extension = file.filename.split('.')[-1]
    filename = f"profile_picture.{file_extension}"

    user_id = current_user['user_id']

    return user_obj.upload_profile_image(Image(image_data=file_data, file_name=filename), user_id)