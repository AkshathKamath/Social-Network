import logging
from typing import Optional
from supabase import create_client, Client, ClientOptions
from httpx import Limits

from app.config import settings

logger = logging.getLogger(__name__)

class SupabaseConnection:
    """Singleton Supabase client with optimized HTTP connection pooling"""
    _client: Optional[Client] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Initialize Supabase client with connection pooling"""
        if cls._initialized:
            return
        
        try:
            logger.info("Initializing Supabase connection")

            options = ClientOptions(
                # HTTP connection pool settings
                postgrest_client_timeout=30,
                storage_client_timeout=30,
                schema="public",
                headers={},
                auto_refresh_token=True,
                persist_session=True,
                # Custom httpx client settings
                flow_type="implicit",
            )
            
            # Create client with custom HTTP limits for connection pooling
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
                options=options
            )
            
            # Test connection with a simple query
            cls._client.table('users').select('*').limit(1).execute()
            logger.info("Supabase connected successfully")
            cls._initialized = True
            
        except Exception as e:
            logger.error(f"Supabase connection failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Could not connect to Supabase: {str(e)}")

    @classmethod
    def get_client(cls) -> Client:
        """Get Supabase client instance"""
        if not cls._initialized or cls._client is None:
            raise RuntimeError("Supabase not initialized. Call initialize() first.")
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close Supabase client and cleanup connections"""
        if cls._client:
            logger.info("Closing Supabase connection")
            try:
                await cls._client.auth.sign_out()
            except Exception as e:
                logger.warning(f"Error during sign out: {e}")
            cls._client = None
            cls._initialized = False
    
    @classmethod
    def health_check(cls) -> bool:
        """Check Supabase health"""
        try:
            if cls._client is None:
                return False
            # Simple query to test connection
            cls._client.table('users').select('count').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

def get_supabase() -> Client:
    """Dependency injection function for FastAPI"""
    return SupabaseConnection.get_client()