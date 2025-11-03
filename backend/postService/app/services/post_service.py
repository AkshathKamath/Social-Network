from app.db.supabase import get_supabase
from app.db.mongo import get_mongo
from app.models.post import Post, PostData, PostUploadResponse, PostFetchResponse, PostDeleteResponse

import uuid
from typing import List
from supabase import Client
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticCollection
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from bson import ObjectId
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
executor = ThreadPoolExecutor(max_workers=10)


class PostService:
## CONSTRUCTOR----------------------------------------------------------------------

    def __init__(self):
        self._supabase: Client = get_supabase()
        self.bucket_name = "user_images"

        self._mongo: AsyncIOMotorClient = get_mongo()
        self._mongo_db = self._mongo['db1']
        self._posts_collection: Collection = self._mongo_db['posts']
        self._precompute_feed_collection: Collection = self._mongo_db['precomputefeed']
    
## HELPER FUNCTIONS-----------------------------------------------------------------
    
    async def _get_followers(
            self,
            user_id: str
    ) -> List[str]:
        """
        Get all followers for a user from Supabase.
        Supabase is still synchronous, so we use thread pool.
        """
        try:
            logger.debug(f"Fetching followers for user {user_id}")
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                executor,
                lambda: self._supabase.table('follows')
                    .select('follower_id')
                    .eq('following_id', user_id)
                    .execute()
            )
            followers = [user['follower_id'] for user in (result.data or [])]
            logger.info(f"Found {len(followers)} followers for user {user_id}")
            return followers
        except Exception as e:
            logger.error(f"Failed to get followers for {user_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Could not fetch followers: {str(e)}")
    
    async def _upload_post_to_storage(
            self,
            file_data: bytes, 
            user_id: str, 
            file_extension: str
    ) -> str:
        """Handle upload image to Supabase storage. Supabase client is sync and blocking operation, so handoff the upload of the image to a separate thread and keep the event loop free to execute other coroutines"""
        try:
            file_name = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = f"{user_id}/{file_name}"
            logger.info(f"Uploading file to storage: {file_path}")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                executor,
                lambda: self._supabase.storage
                    .from_(self.bucket_name)
                    .upload(
                        path=file_path,
                        file=file_data,
                        file_options={"content-type": f"image/{file_extension}"}
                    )
            )
            blob_url = self._supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            logger.info(f"File uploaded successfully: {blob_url}")
            return blob_url
        except Exception as e:
            logger.error(f"Failed to upload to storage: {str(e)}", exc_info=True)
            raise RuntimeError(f"Storage upload failed: {str(e)}")

    async def _upload_post_metadata(
            self,
            user_id: str,
            blob_url: str,
            caption: str,
            created_at: datetime
    ) -> str:
        """
        Insert post metadata into MongoDB
        """
        try:
            logger.info(f"Creating post metadata for user {user_id}")
            post = Post(
                user_id=user_id,
                post_url=blob_url,
                caption=caption,
                created_at=created_at
            )
            result = await self._posts_collection.insert_one(post.model_dump())
            post_id = str(result.inserted_id)
            logger.info(f"Post metadata created: {post_id}")
            return post_id
        except PyMongoError as e:
            logger.error(f"MongoDB error creating post: {str(e)}", exc_info=True)
            raise RuntimeError(f"Database error: {str(e)}")

    async def _push_post_to_followers(
            self,
            post_id: str,
            created_at: datetime,
            followers: List[str]
    ) -> None:
            """
            Push post to all followers' feeds.
            """
            try:
                if not followers:
                    logger.info("No followers to push to")
                    return
                logger.info(f"Pushing post {post_id} to {len(followers)} followers")
                documents = [
                {
                    "user_id": follower_id,
                    "post_id": ObjectId(post_id),
                    "created_at": created_at
                }
                for follower_id in followers
                ]
                result = await self._precompute_feed_collection.insert_many(
                documents,
                ordered=False
                )
                logger.info(f"Post {post_id} pushed to {len(result.inserted_ids)} feeds successfully")
            except PyMongoError as e:
                logger.error(f"Failed to push to feeds: {str(e)}", exc_info=True)
                raise RuntimeError(f"Feed push failed: {str(e)}")

##----------------------------------------------------------------------------------

## MAIN FUNCTIONS-------------------------------------------------------------------

    async def upload_post(
            self, 
            postData: PostData, 
            user_id: str
    ) -> PostUploadResponse:
        created_at = datetime.now()
        try:
            logger.info(f"Starting post upload for user {user_id}")
            # STEP 1: Upload to storage
            blob_url = await self._upload_post_to_storage(
                file_data=postData.image_data,
                user_id=user_id,
                file_extension=postData.file_extension
            )
            # STEP 2: Upload post metadata to posts collection in mongo
            post_id = await self._upload_post_metadata(
                user_id=user_id,
                blob_url=blob_url,
                caption=postData.caption,
                created_at=created_at
            )
            ## STEP 3: Get followers of the current user
            followers = await self._get_followers(
                user_id=user_id
            )
            ## STEP 4: Push post to followers' feed
            await self._push_post_to_followers(
                post_id=post_id,
                created_at=created_at,
                followers=followers
            )
            logger.info("New post pushed to feed table for followers successfully")
            return PostUploadResponse(
                post_id=post_id,
                message="Post Created Successfully"
            )
        except Exception as e:
            logger.error(f"Post upload failed, initiating rollback: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to upload post: {str(e)}")
    
    async def get_post(
            self, 
            user_id: str
    ) -> List[PostFetchResponse]:
        try:
            logger.info(f"Fetching posts for user {user_id}")
            cursor = self._posts_collection.find({"user_id": user_id}) \
                .sort("created_at", -1)
            documents = await cursor.to_list()
            posts = [
                PostFetchResponse(
                    post_id=str(doc['_id']),
                    user_id=doc['user_id'],
                    post_url=doc['post_url'],
                    caption=doc['caption'],
                    created_at=doc['created_at']
                )
                for doc in documents
            ]
            logger.info(f"Retrieved {len(posts)} posts for user {user_id}")
            return posts
        except PyMongoError as e:
            logger.error(f"Database error fetching posts: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to fetch posts: {str(e)}")

    async def delete_post(
            self,
            post_id: str,
            user_id: str
    ) -> PostDeleteResponse:
        """
        Delete post with cleanup
        """
        try:
            logger.info(f"Deleting post {post_id} for user {user_id}")
            # STEP 1: Remove from posts collection
            doc = await self._posts_collection.find_one_and_delete({
                "_id": ObjectId(post_id),
                "user_id": user_id
            })
            if not doc:
                raise ValueError(f"Post {post_id} not found or unauthorized")
            # STEP 2: Remove from storage
            file_path_parts = doc['post_url'].split('/')
            file_name = file_path_parts[-1].split('?')[0]
            full_path = f"{user_id}/{file_name}"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                executor,
                lambda: self._supabase.storage
                    .from_(self.bucket_name)
                    .remove([full_path])
            )
            # STEP 3: Remove from feeds table
            await self._precompute_feed_collection.delete_many({
                "post_id": ObjectId(post_id)
            })
            logger.info(f"Post {post_id} deleted successfully")
            return PostDeleteResponse(
                message=f"Post {post_id} deleted successfully"
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to delete post: {str(e)}")

##----------------------------------------------------------------------------------

## COMPENSATION FUNCTIONS-------------------------------------------------------------


# Factory pattern function
def get_post_service() -> PostService:
    """Create new instance per request"""
    return PostService()