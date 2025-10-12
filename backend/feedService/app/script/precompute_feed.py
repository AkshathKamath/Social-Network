from app.db.database import get_db
from app.db.mongo import get_mongo
from app.models.feed import Post

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pymongo import UpdateOne, DESCENDING
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PreComputeFeed():
    def __init__(self):
        self.db = get_db()
        mongo = get_mongo()
        mongoDb = mongo['db1']
        self.postsCollection = mongoDb['posts']
        self.feedCollecttion = mongoDb['precomputefeed']
        self._create_index()

    def _create_index(self):
        self.feedCollecttion.create_index(
            [("user_id", 1), ("post_id", 1)],
            unique=True
        )
        self.feedCollecttion.create_index(
            [("user_id", 1), ("created_at", DESCENDING)]
        )
        self.postsCollection.create_index(
            [("user_id", 1), ("created_at", DESCENDING)]
        )
    
    def _get_users(self) -> List[str]:
        try:
            result = self.db.table('users').select('id').execute()
            return [user['id'] for user in (result.data or [])]
        except Exception as e:
            logger.error(f"Failed to fetch users: {str(e)}", exc_info=True)
            raise
    
    def _create_follower_following_map(self, users: List[str]) -> Dict[str, List[str]]:
        try:
            result = self.db.table('follows')\
            .select('follower_id, following_id')\
            .in_('follower_id', users)\
            .execute()
            follower_following_map = {}
            for row in (result.data or []):
                follower_id = row['follower_id']
                following_id = row['following_id']
                if follower_id not in follower_following_map:
                    follower_following_map[follower_id] = []
                follower_following_map[follower_id].append(following_id)
            return follower_following_map
        except Exception as e:
            logger.error(f"Failed to fetch following relationships: {str(e)}", exc_info=True)
            raise
    
    def _get_posts(self, creators: List[str], posts_per_creator: int=5) -> Dict[str, List[Dict]]:
        try:
            cutoff_time = datetime.now() - timedelta(days=60)
            pipeline = [
            {
                "$match": {
                    "user_id": {"$in": creators},
                    "created_at": {"$gte": cutoff_time}
                }
            },
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$user_id",
                    "posts": {
                        "$push": {
                            "post_id": "$_id",
                            "created_at": "$created_at"
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "posts": {"$slice": ["$posts", posts_per_creator]}
                }
            }
        ]
            results = self.postsCollection.aggregate(pipeline)
            posts_by_creator = {}
            for doc in results:
                creator_id = doc['_id']
                posts_by_creator[creator_id] = doc['posts']
            return posts_by_creator
        except Exception as e:
            logger.error(f"Failed to fetch posts for creators: {str(e)}", exc_info=True)
            raise
    
    def _update_feed_table(self, feeds: List[Dict]) -> None:
        try:
            if not feeds:
                return
            operations = [
                UpdateOne(
                    {
                "user_id": item['user_id'],
                "post_id": item['post_id']
                },
                {
                "$set": {
                    "created_at": item['created_at'],
                    "updated_at": datetime.now()
                    }
                },
                upsert=True
                )
                for item in feeds
            ]
            result = self.feedCollecttion.bulk_write(operations, ordered=False)
            return
        except Exception as e:
            logger.error(f"Failed to update feeds table: {str(e)}", exc_info=True)
            raise

    def computeFeed(self, batch_size: int=2) -> None:
        try:
            logger.info("Starting Feed table updation")
            users = self._get_users()
            logger.info(f"Processing {len(users)} users")
            for i in range(0, len(users), batch_size):
                users_batch = users[i : i + batch_size]
                logger.info(f"Processing {len(users_batch)} users")
                follower_following_map = self._create_follower_following_map(users=users_batch)
                logger.info(f"Created follower-following map")
                all_creators = set()
                for following_list in follower_following_map.values():
                    all_creators.update(following_list)
                if not all_creators:
                    continue
                posts = self._get_posts(list(all_creators))
                logger.info("Bulk fetched posts for all creators that are followed by users in the batch")
                feed = []
                for user_id in users_batch:
                    following_list = follower_following_map.get(user_id, [])
                    for creator_id in following_list:
                        posts_by_creator = posts.get(creator_id, [])
                        for post in posts_by_creator:
                            feed.append({
                                "user_id": user_id,
                                "post_id": ObjectId(post['post_id']),
                                "created_at": post['created_at']
                            })
                logger.info("Computed feed for batch of users and now pushing bulk write to DB")
                self._update_feed_table(feed)
                logger.info("Pushed feed of current batch to DB")
        except Exception as e:
            logger.error(f"Couldnt compute feed: {str(e)}", exc_info=True)
            raise

precomputefeed_obj = PreComputeFeed()