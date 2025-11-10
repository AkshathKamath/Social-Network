import logging
from typing import Optional
from supabase import Client
import asyncio

from app.db.supabase import get_supabase, _storage_executor

logger = logging.getLogger(__name__)

class StorageService:
## CONSTRUCTOR----------------------------------------------------------------------

    def __init__(self):
        self._supabase: Client = get_supabase()
        self.bucket_name = "user_images"

## MAIN FUNCTIONS-------------------------------------------------------------------

    async def upload_to_storage(
            self,
            file_data: bytes, 
            file_path:str,
            file_extension: str
    ) -> str:
        """Handle upload image to Supabase storage. Supabase client is sync and blocking operation, so handoff the upload of the image to a separate thread and keep the event loop free to execute other coroutines"""
        try:
            logger.info(f"Uploading file to storage: {file_path}")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                _storage_executor,
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
            logger.error(f"Failed to upload file: {str(e)}", exc_info=True)
            raise RuntimeError(f"Storage upload failed: {str(e)}")
    
    async def delete_from_storage(self, file_path: str) -> bool:
        """Handle delete image from Supabase storage. Supabase client is sync and blocking operation, so handoff the delete of the image to a separate thread and keep the event loop free to execute other coroutines"""
        try:
            logger.info(f"Deleting file from storage: {file_path}")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                _storage_executor,
                lambda: self._supabase.storage
                    .from_(self.bucket_name)
                    .remove([file_path])
            )
            logger.info(f"File deleted successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}", exc_info=True)
            raise RuntimeError(f"Storage delete failed: {str(e)}")

def get_storage_service() -> StorageService:
    """Factory function for dependency injection"""
    return StorageService()
    

