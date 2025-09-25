from app.db.database import get_db
from app.db.mongo import get_mongo
from app.models.post import Post, PostData, PostUploadResponse, PostFetchResponse, PostDeleteResponse
import uuid
from typing import List
from bson import ObjectId

class PostService:
    def __init__(self):
        self.db = get_db()
        self.mongo = get_mongo()
        self.bucket_name = "user_images"
        self.database = self.mongo['db1']
        self.collection = self.database['posts']
    
    def upload_post(self, postData: PostData, user_id: str) -> PostUploadResponse:
        try:
            file_name = uuid.uuid4().hex
            file_path = f"{user_id}/{file_name}"
            uploadToS3 = self.db.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=postData.image_data,
                file_options={"content-type": "image/jpeg"}
            )
            if uploadToS3:
                post_url = self.db.storage.from_(self.bucket_name).get_public_url(file_path)
                post = Post(
                    user_id=user_id,
                    post_url=post_url,
                    caption=postData.caption
                )
                result = self.collection.insert_one(post.model_dump())
                return PostUploadResponse(
                    post_id=str(result.inserted_id),
                    message="Post Created Successfully"
                )
        except Exception as e:
            raise Exception(f"Failed to create post: {str(e)}")
    
    def get_post(self, user_id: str) -> List[PostFetchResponse]:
        try:
            cursor = self.collection.find({"user_id": user_id})
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
            doc = self.collection.find_one_and_delete({"_id": ObjectId(post_id), "user_id": user_id})
            file_name = doc['post_url'].split('/')[-1].rstrip('?')
            self.db.storage.from_(self.bucket_name).remove([user_id + "/" + file_name])
            return PostDeleteResponse(
                message=f"Post {post_id} deleted successfully"
        )
        except Exception as e:
            raise Exception(f"Failed to delete post {post_id}: {str(e)}")


post_obj = PostService()