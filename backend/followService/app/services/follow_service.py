# app/services/follow_service.py
from app.db.database import get_db
from typing import Optional, List, Dict

class FollowService():
    def __init__(self):
        self.db = get_db()

    def follow_user(self, follower_id: str, following_id: str) -> bool:
        """Follow a user"""
        
        # Check if already following
        existing = self.db.table('follows').select("id").eq(
            'follower_id', follower_id
        ).eq('following_id', following_id).execute()
        
        if existing.data:
            raise ValueError("Already following this user")
        
        # Check not following self
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")
        
        # Create follow relationship
        result = self.db.table('follows').insert({
            'follower_id': follower_id,
            'following_id': following_id
        }).execute()
        
        return bool(result.data)

    def unfollow_user(self, follower_id: str, following_id: str) -> bool:
        """Unfollow a user"""
        
        # Delete follow relationship
        result = self.db.table('follows').delete().eq(
            'follower_id', follower_id
        ).eq('following_id', following_id).execute()
        
        if not result.data:
            raise ValueError("Not following this user")
        
        return True

    def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict:
        """Get list of followers for a user"""

        # Get followers with user info
        result = self.db.table('follows').select(
            'follower_id, created_at, users!follows_follower_id_fkey(id, email, full_name)'
        ).eq('following_id', user_id).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = self.db.table('follows').select('*', count='exact', head=True).eq('following_id', user_id).execute()
        
        return {
            'followers': result.data if result.data else [],
            'count': count_result.count if count_result else 0
        }

    def get_following(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict:
        """Get list of users that a user follows"""
        
        # Get following with user info
        result = self.db.table('follows').select(
            'following_id, created_at, users!follows_following_id_fkey(id, user_name)'
        ).eq('follower_id', user_id).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_result = self.db.table('follows').select('*', count='exact', head=True).eq('follower_id', user_id).execute()
        
        return {
            'following': result.data if result.data else [],
            'count': count_result.count if count_result else 0
        }

    def check_relationship(self, user_id: str, target_id: str) -> Dict:
        """Check follow relationship between two users"""
        
        # Check if user follows target
        following = self.db.table('follows').select('id').eq(
            'follower_id', user_id
        ).eq('following_id', target_id).execute()
        
        # Check if target follows user
        followed_by = self.db.table('follows').select('id').eq(
            'follower_id', target_id
        ).eq('following_id', user_id).execute()
        
        return {
            'following': bool(following.data),
            'followed_by': bool(followed_by.data)
        }

follow_service_object = FollowService()