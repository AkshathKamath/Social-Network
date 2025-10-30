# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.db.mongo import MongoDBConnection
from app.db.supabase import SupabaseConnection
from app.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Application starting...")
    try:
        MongoDBConnection.initialize()
        SupabaseConnection.initialize()
        logger.info("All connections initialized")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    try:
        MongoDBConnection.close()
        SupabaseConnection.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Post management service",
    lifespan=lifespan
)

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Include routers
from app.api import posts
app.include_router(posts.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"service": "Posts Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mongo_healthy = MongoDBConnection.health_check()
    supabase_healthy = SupabaseConnection.health_check()
    if not mongo_healthy:
        return {"status": "unhealthy", "mongodb": "down"}, 503
    if not supabase_healthy:
        return {"status": "unhealthy", "supabase": "down"}, 503
    return {"status": "healthy", "mongodb": "up", "supabase": "up"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=4002, reload=True)