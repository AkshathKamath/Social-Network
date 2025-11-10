import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

class PostgreSQLConnection:
    """
    Async PostgreSQL connection manager using SQLAlchemy 2.0.
    """
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    _initialized: bool = False

    @classmethod
    async def initialize(cls):
        """
        Initialize async PostgreSQL engine with connection pooling.
        """
        if cls._initialized:
            logger.warning("PostgreSQL connection already initialized")
            return
        try:
            logger.info(f"Initializing async PostgreSQL connection")
            
            # Create async engine
            cls._engine = create_async_engine(
                settings.postgres_url,
                poolclass=QueuePool,
                pool_size=settings.postgres_pool_size,     
                max_overflow=settings.postgres_max_overflow, 
                pool_pre_ping=True,
                pool_recycle=3600, 
                echo=False,
                future=True, 
                connect_args={
                    "statement_cache_size": 0,
                    "server_settings": {
                        "application_name": "posts_service",
                    },
                    "command_timeout": 60,   
                    "timeout": 10, 
                },
            ) 
            cls._session_factory = async_sessionmaker(
                cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autoflush=False,         # Manual control over flushing
                autocommit=False,        # Explicit transactions
            )
            async with cls._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL connected successfully")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}", exc_info=True)
            raise RuntimeError(f"PostgreSQL connection failed: {str(e)}")  
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Get the async engine"""
        if not cls._initialized or cls._engine is None:
            raise RuntimeError("PostgreSQL not initialized")
        return cls._engine

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        """Get the session factory"""
        if not cls._initialized or cls._session_factory is None:
            raise RuntimeError("PostgreSQL not initialized")
        return cls._session_factory

    @classmethod
    async def close(cls):
        """Close all connections"""
        if cls._engine is not None:
            logger.info("Closing PostgreSQL connections")
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            cls._initialized = False
    
    @classmethod
    async def health_check(cls) -> bool:
        """Check if PostgreSQL is healthy"""
        try:
            if cls._engine is None:
                return False
            async with cls._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {str(e)}")
            return False
    
    # Dependency injection for sessions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Automatically handles commit/rollback and cleanup.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    session_factory = PostgreSQLConnection.get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise
        finally:
            await session.close()

# Convenience function for getting engine
def get_engine() -> AsyncEngine:
    """Get the async engine for raw SQL if needed"""
    return PostgreSQLConnection.get_engine()