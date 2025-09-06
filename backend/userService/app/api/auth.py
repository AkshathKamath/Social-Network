from fastapi import APIRouter, HTTPException
from app.models.user import UserRegister, UserLogin
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
            "email": user['email']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login(login_data: UserLogin):
    """Login user"""
    user = auth_service.login_user(login_data)
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    
    return {
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name']
        }
    }