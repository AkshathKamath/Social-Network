from app.db.database import get_db
from app.db.mongo import get_mongo
from app.models.post import Post, PostData,PostResponse
import uuid
from datetime import datetime

class PostService:
    def __init__(self):
        self.db = get_db()
        self.mongo = get_mongo()
        self.bucket_name = "user_images"
        self.database = self.mongo['db1']
        self.collection = self.database['posts']
    
    def upload_post(self, postData: PostData, user_id: str) -> PostResponse:
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
                return PostResponse(
                    post_id=str(result.inserted_id),
                    message="Post Created Successfully"
                )
        except Exception as e:
            raise Exception(f"Failed to create post: {str(e)}")

post_obj = PostService()