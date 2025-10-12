from app.db.database import get_db
from app.db.mongo import get_mongo
from app.models.feed import Post

from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FeedService():
    def __init__(self):
        self.db = get_db()
        mongo = get_mongo()
        mongoDatabase = mongo['db1']
        self.postsCollection = mongoDatabase['posts']
        self.precomputeFeedCollection = mongoDatabase['precomputefeed']
    
    def generate_feed(self, user_id: str, timestamp: datetime = None) -> List[Post]:
        try:
            timestamp = timestamp or datetime.now()
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$lt": timestamp}
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$limit": 5},
                {
                    "$lookup": {
                        "from": "posts",
                        "localField": "post_id",
                        "foreignField": "_id",
                        "as": "post_data"
                    }
                },
                {"$unwind": "$post_data"},
                {
                    "$project": {
                        "_id": "$post_data._id",
                        "user_id": "$post_data.user_id",
                        "post_url": "$post_data.post_url",
                        "caption": "$post_data.caption",
                        "created_at": "$post_data.created_at"
                    }
                },
            ]
            cursor = self.precomputeFeedCollection.aggregate(pipeline)
            logger.info(f"Created Feed for user: {user_id}")
            posts = [
                Post(
                    post_id=str(doc['_id']),
                    user_id=doc['user_id'],
                    post_url=doc['post_url'],
                    caption=doc['caption'],
                    created_at=doc['created_at']
                )
                for doc in cursor
            ]
            return posts
        except Exception as e:
            logger.error(f"Couldn't generate feed for user: {user_id} {str(e)}")
            raise
        

feed_service_obj = FeedService()