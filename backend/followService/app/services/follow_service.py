# app/services/follow_service.py
from app.db.database import get_db
from app.db.cache import get_redis
from app.models.follow import FollowResponse, FollowersResponse, FollowingResponse, User
from typing import Optional, List, Dict

class FollowService():
    def __init__(self):
        self.db = get_db()
        self.redis = get_redis()

    def follow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Follow a user"""

        # Check not following self
        if follower_id == following_id:
            raise ValueError("Cannot follow yourself")
        
        # Check if already following
        existing = self.db.table('follows').select("id").eq(
            'follower_id', follower_id
        ).eq('following_id', following_id).execute()
        
        if existing.data:
            raise ValueError("Already following this user")
        
        # Invalidate the cache
        print("User deleted from cache") if self.redis.delete(f"user:{follower_id}") else None
        #
        
        # Create follow relationship
        result = self.db.table('follows').insert({
            'follower_id': follower_id,
            'following_id': following_id
        }).execute()
        
        return FollowResponse(
            message="Successfully followed user",
            following= bool(result.data)
        )
        

    def unfollow_user(self, follower_id: str, following_id: str) -> FollowResponse:
        """Unfollow a user"""

        # Invalidate the cache
        print("User deleted from cache") if self.redis.delete(f"user:{follower_id}") else None
        
        # Delete follow relationship
        result = self.db.table('follows').delete().eq(
            'follower_id', follower_id
        ).eq('following_id', following_id).execute()
        
        if not result.data:
            raise ValueError("Not following this user")
        
        return FollowResponse(
            message="Successfully unfollowed user",
            following= not bool(result.data) 
        )


    def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> FollowersResponse:
        """Get list of followers for a user"""

        # Get followers with user info
        result = self.db.table('follows').select(
            'users!follows_follower_id_fkey(id, full_name, user_name)'
        ).eq('following_id', user_id).range(offset, offset + limit - 1).execute()

        followers = []
        if result.data:
            for item in result.data:
                user_info = item.get('users', {})
                followers.append(User(
                    user_id=user_info.get['id'],
                    full_name=user_info.get('full_name'),
                    user_name=user_info.get('user_name')
                ))
            
        return FollowersResponse(
            followers=followers
        )


    def get_following(self, user_id: str, limit: int = 50, offset: int = 0) -> FollowingResponse:
        """Get list of users that a user follows"""
        
        # Get following with user info
        result = self.db.table('follows').select(
            'users!follows_following_id_fkey(id, full_name, user_name)'
        ).eq('follower_id', user_id).range(offset, offset + limit - 1).execute()
        
        following = []
        if result.data:
            for item in result.data:
                user_info = item.get('users', {})
                following.append(User(
                    user_id=user_info.get('id'),
                    full_name=user_info.get('full_name'),
                    user_name=user_info.get('user_name')
                ))

        return FollowingResponse(
            following=following
        )

follow_service_object = FollowService()