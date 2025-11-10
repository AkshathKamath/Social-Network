from app.db.mongo import get_mongo
from app.db.postgres import get_db_session
from app.models.post import Post, PostData, PostUploadResponse, PostFetchResponse, PostDeleteResponse
from app.services.storage_service import StorageService, get_storage_service

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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import Depends

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PostService:
## CONSTRUCTOR----------------------------------------------------------------------

    def __init__(
            self,
            storage_service: StorageService,
            db_session: AsyncSession
    ):
        self._db_session = db_session

        self._mongo: AsyncIOMotorClient = get_mongo()
        self._mongo_db = self._mongo['db1']
        self._posts_collection: Collection = self._mongo_db['posts']
        self._precompute_feed_collection: Collection = self._mongo_db['precomputefeed']

        self._storage_service = storage_service

        self._saga_state = {
            'blob_url': None,
            'post_id': None,
            'feed_pushed': False
        }
    
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
            from app.models.db_models import Follow
            query = select(Follow.follower_id).where(Follow.following_id == user_id)
            result = await self._db_session.execute(query)
            followers = [row[0] for row in result.fetchall()]
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
        try:
            file_name = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = f"{user_id}/{file_name}"
            blob_url = self._storage_service.upload_to_storage(
                file_data=file_data,
                file_path=file_path,
                file_extension=file_extension
            )
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
    
    async def _delete_post_metadata(
            self,
            post_id: str,
            user_id: str
    ) -> str:
        """
        Delete post metadata from MongoDB
        """
        try:
            logger.info(f"Deleting post metadata {post_id} for user {user_id}")
            result = await self._posts_collection.delete_one({
                "_id": ObjectId(post_id),
                "user_id": user_id
            })
            if result.deleted_count == 0:
                raise ValueError(f"Post {post_id} not found or unauthorized")
            logger.info(f"Post metadata {post_id} deleted successfully")
            return result['post_url']
        except ValueError:
            raise
        except PyMongoError as e:
            logger.error(f"MongoDB error deleting post: {str(e)}", exc_info=True)
            raise RuntimeError(f"Database error: {str(e)}"
    )

    async def _delete_post_from_storage(
            self,
            post_url: str
    ) -> None:
        """
        Delete post from Supabase storage
        """
        try:
            file_path_parts = post_url.split('/')
            file_name = file_path_parts[-1].split('?')[0]
            user_id = file_path_parts[-2]
            full_path = f"{user_id}/{file_name}"
            await self._storage_service.delete_from_storage(
                file_path=full_path
            )
            logger.info(f"Post deleted from storage: {full_path}")
        except Exception as e:
            logger.error(f"Failed to delete from storage: {str(e)}", exc_info=True)
            raise RuntimeError(f"Storage delete failed: {str(e)}")
    
    async def _remove_post_from_feeds(
            self,
            post_id: str
    ) -> None:
        """
        Remove post from all followers' feeds
        """
        try:
            logger.info(f"Removing post {post_id} from all feeds")
            result = await self._precompute_feed_collection.delete_many({
                "post_id": ObjectId(post_id)
            })
            logger.info(f"Post {post_id} removed from {result.deleted_count} feeds successfully")
        except PyMongoError as e:
            logger.error(f"Failed to remove post from feeds: {str(e)}", exc_info=True)
            raise RuntimeError(f"Feed removal failed: {str(e)}")
        

## COMPENSATION FUNCTIONS-------------------------------------------------------------




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
            post_url = await self._delete_post_metadata(
                post_id=post_id,
                user_id=user_id
            )
            # STEP 2: Delete from storage
            await self._delete_post_from_storage(
                post_url=post_url
            )
            # STEP 3: Remove from feeds table
            await self._remove_post_from_feeds(
                post_id=post_id
            )
            logger.info(f"Post {post_id} deleted successfully")
            return PostDeleteResponse(
                message="Post Deleted Successfully"
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to delete post: {str(e)}")

##----------------------------------------------------------------------------------


# Factory pattern function
def get_post_service(
    db_session: AsyncSession = Depends(get_db_session),
    storage_service: StorageService = Depends(get_storage_service)
) -> PostService:
    """Create new instance per request"""
    return PostService(db_session, storage_service)