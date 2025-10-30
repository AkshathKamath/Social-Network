from app.db.supabase import get_supabase
from app.db.mongo import get_mongo
from app.models.post import Post, PostData, PostUploadResponse, PostFetchResponse, PostDeleteResponse

import uuid
from typing import List
from supabase import Client
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from bson import ObjectId
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PostService:
    def __init__(self):
        self.supabase: Client = get_supabase()
        self.bucket_name = "user_images"

        self._mongo_client: MongoClient = get_mongo()
        self._mongo_db = self._mongo_client['db1']
        self._posts_collection: Collection = self._mongo_db['posts']
        self._precompute_feed_collection: Collection = self._mongo_db['precomputefeed']
    
## HELPER FUNCTIONS-----------------------------------------------------------------
    
    def _get_followers(self, user_id: str) -> List[str]:
        try:
            result = self.supabase.table('follows').select('follower_id').eq('following_id', user_id).execute()
            return [user['follower_id'] for user in (result.data or [])]
        except Exception as e:
            logger.error(f"Couldn't get followers for {user_id}: {str(e)}")
            raise
    
    def _push_post_to_followers(self, user_id: str, post_id: str, created_at: datetime, followers: List[str]) -> None:
        try:
           documents = [
                {
                     "user_id": follower,
                     "post_id": ObjectId(post_id),
                     "created_at": created_at
                }
                for follower in followers
           ]
           if documents:
                result = self._precompute_feed_collection.insert_many(documents)
           return
        except Exception as e:
            logger.error(f"Couldn't push post to all folowers for {user_id}: {str(e)}")
            raise

##----------------------------------------------------------------------------------

## MAIN FUNCTIONS-------------------------------------------------------------------

    def upload_post(self, postData: PostData, user_id: str, timestamp: datetime = None) -> PostUploadResponse:
        try:
            file_name = uuid.uuid4().hex
            file_path = f"{user_id}/{file_name}"
            uploadToS3 = self.supabase.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=postData.image_data,
                file_options={"content-type": "image/jpeg"}
            )
            if uploadToS3:
                post_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                timestamp = timestamp or datetime.now()
                post = Post(
                    user_id=user_id,
                    post_url=post_url,
                    caption=postData.caption,
                    created_at=timestamp
                )
                result = self._posts_collection.insert_one(post.model_dump())
                followers = self._get_followers(user_id)
                self._push_post_to_followers(user_id, str(result.inserted_id), timestamp, followers)
                logger.info("New post pushed to feed table for followers successfully")
                return PostUploadResponse(
                    post_id=str(result.inserted_id),
                    message="Post Created Successfully"
                )
        except Exception as e:
            raise Exception(f"Failed to create post: {str(e)}")
    
    def get_post(self, user_id: str) -> List[PostFetchResponse]:
        try:
            cursor = self._posts_collection.find({"user_id": user_id})
            posts = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                posts.append(doc)
            return [
                PostFetchResponse(
                    post_id=post['_id'],
                    user_id=post['user_id'],
                    post_url=post['post_url'],
                    caption=post['caption'],
                    created_at=post['created_at']
                )
                for post in posts
            ]
        except Exception as e:
            raise Exception(f"Failed to fetch posts for user {user_id}: {str(e)}")

    def delete_post(self, post_id: str, user_id: str) -> PostDeleteResponse:
        try:
            doc = self._posts_collection.find_one_and_delete({"_id": ObjectId(post_id), "user_id": user_id})
            file_name = doc['post_url'].split('/')[-1].rstrip('?')
            self.db.storage.from_(self.bucket_name).remove([user_id + "/" + file_name])
            return PostDeleteResponse(
                message=f"Post {post_id} deleted successfully"
        )
        except Exception as e:
            raise Exception(f"Failed to delete post {post_id}: {str(e)}")

##----------------------------------------------------------------------------------


# Factory pattern function
def get_post_service() -> PostService:
    """Create new instance per request"""
    return PostService()