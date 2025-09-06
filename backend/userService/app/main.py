from fastapi import FastAPI
from app.api import auth

app = FastAPI(title="User Service", version="1.0.0")

# Include the auth router
app.include_router(auth.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "User Service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=4000,
        reload=True
    )