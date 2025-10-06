from app.db.database import get_db
from app.db.mongo import get_mongo
from app.models.feed import Post
from typing import List

class FeedService():
    def __init__(self):
        self.db = get_db()
        self.mongo = get_mongo()
        self.database = self.mongo['db1']
        self.collection = self.database['posts']
    
    def _get_following(self, user_id: str) -> List:
        try:
            result = self.db.table('follows').select('following_id').eq('follower_id', user_id).execute()
            if result.data:
                return [
                    following['following_id']
                for following in result.data
                ]
        except Exception as e:
            raise Exception(f"Failed to fetch list of users following: {str(e)}")
    
    def generate_feed(self, user_id: str) -> List[Post]:
        try:
            followingUsers = self._get_following(user_id=user_id)
            if not followingUsers:
                return []
            cursor = self.collection.find(
            {"user_id": {"$in": followingUsers}},
            sort=[("created_at", -1)]
            )
            posts = []
            for doc in cursor:
                    doc['_id'] = str(doc['_id'])
                    posts.append(
                        Post(
                            post_id=doc['_id'],
                            user_id=doc['user_id'],
                            post_url=doc['post_url'],
                            caption=doc['caption'],
                            created_at=doc['created_at']
                        )
                    )
            return posts
        except Exception as e:
            print(f"Cannot generate feed for user : {user_id} due to {str(e)}")
        

feed_service_obj = FeedService()