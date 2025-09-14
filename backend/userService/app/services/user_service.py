from app.db.database import get_db
from app.models.user import Image, Message

class UserService():
    def __init__(self):
        self.db = get_db()
        self.bucket_name = "user_images"
    
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