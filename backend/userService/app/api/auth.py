from fastapi import APIRouter, HTTPException
from app.db.database import get_db
from app.models.user import User, UserRegister, UserLogin
from app.models.token import Token, RefreshToken, LogoutMessage
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

## /register
@router.post("/register", response_model=User)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        return auth_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

## /login
@router.post("/login", response_model=User)
async def login(login_data: UserLogin):
    """Login user"""
    result = auth_service.login_user(login_data)
    
    if not result:
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    return result

## /logout
@router.post("/logout", response_model=LogoutMessage)
async def logout(request: RefreshToken):
    """
    Logout user by revoking refresh token
    """
    result = auth_service.logout_user(request)

    if not result:
        raise HTTPException(
            status_code=401, 
            detail="Invalid Refresh token"
        )
    return result

## /refresh
@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshToken):
    """Create new access token by sending the refresh token"""
    try:
        return auth_service.refresh_token(request)
    except ValueError as e:
        # All ValueErrors become 401 Unauthorized
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to refresh token")