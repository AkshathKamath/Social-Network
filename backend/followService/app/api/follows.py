# app/api/follows.py
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_user
from app.services import follow_service
from app.models.follow import FollowResponse, FollowersResponse, FollowingResponse, RelationshipResponse
from typing import Dict

router = APIRouter(prefix="/follows", tags=["Follows"])

@router.post("/{user_id}", response_model=FollowResponse)
async def follow_user(
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Follow a user"""
    try:
        follow_service.follow_user(current_user['user_id'], user_id)
        return FollowResponse(message="Successfully followed user", following=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", response_model=FollowResponse)
async def unfollow_user(
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Unfollow a user"""
    try:
        follow_service.unfollow_user(current_user['user_id'], user_id)
        return FollowResponse(message="Successfully unfollowed user", following=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/followers", response_model=FollowersResponse)
async def get_my_followers(
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get current user's followers"""
    result = follow_service.get_followers(current_user['user_id'], limit, offset)
    return FollowersResponse(**result)

@router.get("/following", response_model=FollowingResponse)
async def get_my_following(
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get users that current user follows"""
    result = follow_service.get_following(current_user['user_id'], limit, offset)
    return FollowingResponse(**result)

@router.get("/users/{user_id}/followers", response_model=FollowersResponse)
async def get_user_followers(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get a user's followers (public)"""
    result = follow_service.get_followers(user_id, limit, offset)
    return FollowersResponse(**result)

@router.get("/users/{user_id}/following", response_model=FollowingResponse)
async def get_user_following(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get users that a user follows (public)"""
    result = follow_service.get_following(user_id, limit, offset)
    return FollowingResponse(**result)

@router.get("/relationship/{target_id}", response_model=RelationshipResponse)
async def check_relationship(
    target_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Check relationship between current user and target user"""
    result = follow_service.check_relationship(current_user['user_id'], target_id)
    return RelationshipResponse(**result)