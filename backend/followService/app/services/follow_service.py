# app/services/follow_service.py
from app.db.database import get_db
from typing import Optional, List, Dict

def follow_user(follower_id: str, following_id: str) -> bool:
    """Follow a user"""
    db = get_db()
    
    # Check if already following
    existing = db.table('follows').select("id").eq(
        'follower_id', follower_id
    ).eq('following_id', following_id).execute()
    
    if existing.data:
        raise ValueError("Already following this user")
    
    # Check not following self
    if follower_id == following_id:
        raise ValueError("Cannot follow yourself")
    
    # Create follow relationship
    result = db.table('follows').insert({
        'follower_id': follower_id,
        'following_id': following_id
    }).execute()
    
    return bool(result.data)

def unfollow_user(follower_id: str, following_id: str) -> bool:
    """Unfollow a user"""
    db = get_db()
    
    # Delete follow relationship
    result = db.table('follows').delete().eq(
        'follower_id', follower_id
    ).eq('following_id', following_id).execute()
    
    if not result.data:
        raise ValueError("Not following this user")
    
    return True

def get_followers(user_id: str, limit: int = 50, offset: int = 0) -> Dict:
    """Get list of followers for a user"""
    db = get_db()
    
    # Get followers with user info
    result = db.table('follows').select(
        'follower_id, created_at, users!follows_follower_id_fkey(id, email, full_name)'
    ).eq('following_id', user_id).range(offset, offset + limit - 1).execute()
    
    # Get total count
    count_result = db.table('follows').select('*', count='exact', head=True).eq('following_id', user_id).execute()
    
    return {
        'followers': result.data if result.data else [],
        'count': count_result.count if count_result else 0
    }

def get_following(user_id: str, limit: int = 50, offset: int = 0) -> Dict:
    """Get list of users that a user follows"""
    db = get_db()
    
    # Get following with user info
    result = db.table('follows').select(
        'following_id, created_at, users!follows_following_id_fkey(id, user_name)'
    ).eq('follower_id', user_id).range(offset, offset + limit - 1).execute()
    
    # Get total count
    count_result = db.table('follows').select('*', count='exact', head=True).eq('follower_id', user_id).execute()
    
    return {
        'following': result.data if result.data else [],
        'count': count_result.count if count_result else 0
    }

def check_relationship(user_id: str, target_id: str) -> Dict:
    """Check follow relationship between two users"""
    db = get_db()
    
    # Check if user follows target
    following = db.table('follows').select('id').eq(
        'follower_id', user_id
    ).eq('following_id', target_id).execute()
    
    # Check if target follows user
    followed_by = db.table('follows').select('id').eq(
        'follower_id', target_id
    ).eq('following_id', user_id).execute()
    
    return {
        'following': bool(following.data),
        'followed_by': bool(followed_by.data)
    }