# app/api/users.py (new file)
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.db.database import get_db
from typing import Dict

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current user's profile
    This endpoint is PROTECTED - requires valid JWT token
    """
    db = get_db()
    
    # Get full user data from database
    result = db.table('users').select("*").eq('id', current_user['user_id']).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = result.data[0]
    user.pop('password_hash', None)  # Remove sensitive data
    
    return {
        "user": user,
        "token_info": {
            "user_id": current_user['user_id'],
            "user_name": current_user['user_name']
        }
    }

@router.put("/me")
async def update_my_profile(
    update_data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update current user's profile
    PROTECTED - requires valid JWT token
    """
    db = get_db()
    
    # Don't allow updating certain fields
    update_data.pop('id', None)
    update_data.pop('email', None)  # Email change should be separate endpoint
    update_data.pop('password_hash', None)
    
    # Update user
    result = db.table('users').update(update_data).eq('id', current_user['user_id']).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = result.data[0]
    user.pop('password_hash', None)
    
    return {"message": "Profile updated", "user": user}

@router.delete("/me")
async def delete_my_account(current_user: Dict = Depends(get_current_user)):
    """
    Delete current user's account
    PROTECTED - requires valid JWT token
    """
    db = get_db()
    
    # Delete user (cascade will delete refresh tokens)
    result = db.table('users').delete().eq('id', current_user['user_id']).execute()
    
    return {"message": "Account deleted successfully"}