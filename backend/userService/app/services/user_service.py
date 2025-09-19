from app.db.database import get_db
from app.db.cache import get_redis
from app.models.user import User, UserUpdate, Image, Message

class UserService():
    def __init__(self):
        self.db = get_db()
        self.redis = get_redis()
        self.bucket_name = "user_images"
    
    def get_user(self, user_id: str) -> User:
        try:
            ## Try to get from cache first
            if self.redis.exists(f"user:{user_id}"):
                print("Fetching from cache")
                user = self.redis.hgetall(f"user:{user_id}")
                user = {k.decode(): v.decode() for k, v in user.items()} # Decode from bytes -> string
                return User(
                    user_id=user_id,
                    full_name=user['full_name'],
                    user_name=user['user_name'],
                    image_url=user['profile_image_url'],
                    followers_count=int(user.get('followers_count', 0)),
                    following_count=int(user.get('following_count', 0))
                )

            ## If not in cache, get from DB
            print("Fetching from DB")
            result = self.db.table('users').select('full_name, user_name, followers_count, following_count, profile_image_url').eq('id', user_id).execute()
            if result.data:
                user = result.data[0]
                # Store in cache for future requests
                print("Storing in cache")
                self.redis.hset(f"user:{user_id}", mapping=user)
                return  User(
                    user_id=user_id,
                    full_name=user['full_name'],
                    user_name=user['user_name'],
                    image_url=user['profile_image_url'],
                    followers_count=int(user.get('followers_count', 0)),
                    following_count=int(user.get('following_count', 0))
                )

        except Exception as e:
            raise Exception(f"Failed to fetch user: {str(e)}")


    def update_user(self, updated_user: UserUpdate, user_id: str) -> User:
        try:
            updated_user = {k: v for k, v in updated_user.items() if v is not None}
            result = self.db.table('users').update(updated_user).eq('id', user_id).execute()
            if result:
                user = result.data[0]
                ## Invalidate the cache
                print("Deleted from cache") if self.redis.delete(f"user:{user_id}") else None
                return User(
                    user_id=user['id'],
                    full_name=user['full_name'],
                    user_name=user['user_name'],
                    image_url=user['profile_image_url'],
                    followers_count=int(user.get('followers_count', 0)),
                    following_count=int(user.get('following_count', 0))
                )
        except Exception as e:
            raise Exception(f"Failed to update user: {user_id} due to {str(e)}")
    
        
    def delete_user(self, user_id: str) -> Message:
        try:
            result = self.db.table('users').delete().eq('id', user_id).execute()
            if bool(result):
                # Invalidate the cache
                print("Deleted from cache") if self.redis.delete(f"user:{user_id}") else None
                return Message(message=f"User: {user_id} deleted successfully")
        except Exception as e:
            raise Exception(f"Failed to delete user: {user_id} due to {str(e)}")
    

    def upload_profile_image(self, image: Image, user_id: str) -> Message:
        try:
            # Check if profile picture exists, if yes then delete older
            image_url = self.db.table("users").select("profile_image_url").eq("id", user_id).execute()
            if image_url.data:
                self.db.storage.from_(self.bucket_name).remove([user_id + "/" + image.file_name])
            # Create unique file path
            file_path = f"{user_id}/{image.file_name}"
            
            # Upload to storage
            result = self.db.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=image.image_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            if result:
                # Get public URL
                public_url = self.db.storage.from_(self.bucket_name).get_public_url(file_path)
                upload_to_db = self.db.table("users").update({
                    "profile_image_url": public_url
                }).eq("id", user_id).execute()
                if bool(upload_to_db):
                    return Message(message="Image uploaded successfully")
                
        except Exception as e:
            raise Exception(f"Failed to upload image: {str(e)}")

user_obj = UserService()