import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)

class MongoDBConnection:
    ## Class variable client and initialized var as we want to create 1 client with a pool of connections
    _client: Optional[AsyncIOMotorClient] = None
    _initialized: bool = False

    @classmethod
    async def initialize(cls):
        """Initialize MongoDB connection pool"""
        ## If client is already initialized, do not create a new one (Singleton Pattern)
        if cls._initialized: 
            logger.warning("MongoDB connection already initialized")
            return
        try:
            logger.info("Initializing MongoDB connection")
            cls._client = AsyncIOMotorClient(
                settings.mongo_url,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,         
                waitQueueTimeoutMS=5000,
                retryWrites=True,            
                retryReads=True,
                appName="instagram_clone",
            )
            # Test connection
            await cls._client.admin.command('ping')
            logger.info("MongoDB connected successfully")
            cls._initialized = True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Could not connect to MongoDB: {str(e)}")
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB server selection timeout: {str(e)}", exc_info=True)
            raise RuntimeError(f"Could not connect to MongoDB server: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}", exc_info=True)
            raise

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get MongoDB client"""
        ## Initialize the client only once and use the same client for all requests. Client consists of a pool of connections that can be reused for requests
        if not cls._initialized or cls._client is None:
            raise RuntimeError("MongoDB not initialized")
        return cls._client
    
    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls._client:
            logger.info("Closing MongoDB connection")
            cls._client.close()
            cls._client = None
            cls._initialized = False
    
    @classmethod
    def health_check(cls) -> bool:
        """Check MongoDB health"""
        try:
            if cls._client is None:
                return False
            cls._client.admin.command('ping')
            return True
        except Exception:
            return False

def get_mongo() -> AsyncIOMotorClient:
    ## Class methods can be directly called without creating a object
    return MongoDBConnection.get_client()