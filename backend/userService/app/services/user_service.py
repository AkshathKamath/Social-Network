from app.db.database import get_db
from app.models.user import User, UserUpdate, Image, Message

class UserService():
    def __init__(self):
        self.db = get_db()
        self.bucket_name = "user_images"
    
    def get_user(self, user_id: str) -> User:
        try:
            result = self.db.table('users').select("*").eq('id', user_id).execute()
            if result.data:
                user = result.data[0]
                user.pop('password_hash', None)
                return User(
                    user_id=user_id,
                    full_name=user['full_name'],
                    user_name=user['user_name'],
                    image_url=user['profile_image_url']
                )

        except Exception as e:
            raise Exception(f"Failed to fetch user: {str(e)}")


    def update_user(self, updated_user: UserUpdate, user_id: str) -> User:
        try:
            updated_user = {k: v for k, v in updated_user.items() if v is not None}
            result = self.db.table('users').update(updated_user).eq('id', user_id).execute()
            if result:
                user = result.data[0]
                return User(
                    user_id=user['id'],
                    full_name=user['full_name'],
                    user_name=user['user_name'],
                    image_url=user['profile_image_url']
                )
        except Exception as e:
            raise Exception(f"Failed to update user: {user_id} due to {str(e)}")
    
        
    def delete_user(self, user_id: str) -> Message:
        try:
            result = self.db.table('users').delete().eq('id', user_id).execute()
            if bool(result):
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