from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from typing import Optional, Dict

# This will extract the Bearer token from the Authorization header
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Dependency to get the current user from JWT token
    
    Usage: Add this to any endpoint that needs authentication
    """
    token = credentials.credentials
    
    # Verify the token
    payload = verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return user info from token
    return {
        "user_id": payload.get("user_id"),
        "user_name": payload.get("user_name")
    }