from fastapi import APIRouter, HTTPException
from app.db.database import get_db
from app.models.user import UserRegister, UserLogin
from app.models.token import LogoutRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        user = auth_service.register_user(user_data)
        return {
            "message": "User registered successfully",
            "user_id": user['id'],
            "email": user['email'],
            "user_name": user['user_name'],
            "full_name": user['full_name']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login(login_data: UserLogin):
    """Login user"""
    result = auth_service.login_user(login_data)
    
    if not result:
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    
    return {
        "access_token": result['access_token'],
        "refresh_token": result['refresh_token'],
        "token_type": result['token_type'],
        "user": {
            "id": result['user']['id'],
            "email": result['user']['email'],
            "full_name": result['user']['full_name']
        }
    }

@router.post("/logout")
async def logout(request: LogoutRequest):
    """
    Logout user by revoking refresh token
    """
    """Logout by revoking refresh token"""
    db = get_db()
    
    result = db.table('refresh_tokens').update({
        "revoked": True
    }).eq('token', request.refresh_token).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Invalid or already revoked token")
    
    return {"message": "Successfully logged out"}