import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app.config import settings

logger = logging.getLogger(__name__)

class MongoDBConnection:
    ## Class variable client and initialized var as we want to create 1 client with a pool of connections
    _client: Optional[MongoClient] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Initialize MongoDB connection pool"""
        ## If client is already initialized, do not create a new one (Singleton Pattern)
        if cls._initialized: 
            return
        try:
            logger.info("Initializing MongoDB connection")
            cls._client = MongoClient(
                settings.mongo_url,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                retryReads=True,
                appName="instagram_clone",
            )
            # Test connection
            cls._client.admin.command('ping')
            logger.info("MongoDB connected successfully")
            cls._initialized = True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Could not connect to MongoDB: {str(e)}")

    @classmethod
    def get_client(cls) -> MongoClient:
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

def get_mongo() -> MongoClient:
    ## Class methods can be directly called without creating a object
    return MongoDBConnection.get_client()