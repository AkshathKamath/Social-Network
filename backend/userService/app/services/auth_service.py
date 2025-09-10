from app.db.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import UserRegister, UserLogin, User
from app.models.token import Token, RefreshToken, LogoutMessage
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone

def register_user(user_data: UserRegister) -> User:
    """Register a new user"""
    db = get_db()
    
    # Check if email already exists
    existing = db.table('users').select("id").eq('email', user_data.email).execute()
    if existing.data:
        raise ValueError("Email already registered")
    
    # Prepare user data with hashed password
    user_dict = user_data.model_dump()
    user_dict['password_hash'] = hash_password(user_dict.pop('password'))
    user_dict['date_of_birth'] = str(user_dict['date_of_birth'])
    
    # Insert into database
    result = db.table('users').insert(user_dict).execute()
    
    if result.data:
        user = result.data[0]
        return User(
            email=user['email'],
            full_name=user['full_name'],
            user_name=user['user_name']
        )
    
    raise Exception("Failed to create user")

def login_user(login_data: UserLogin) -> User:
    """Authenticate user and return user data if successful"""
    db = get_db()
    
    # Get user by email
    result = db.table('users').select("*").eq('email', login_data.email).execute()
    
    if not result.data:
        return None  # User not found
    
    user = result.data[0]
    
    # Verify password
    if not verify_password(login_data.password, user['password_hash']):
        return None  # Wrong password
    
    token_data = {
            "user_id": user['id'],
            "user_name": user['user_name']
        }
        
        # Generate tokens
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Store refresh token in database
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    db.table('refresh_tokens').insert({
        "user_id": user['id'],
        "token": refresh_token,
        "expires_at": expires_at.isoformat()
    }).execute()
    
    # Remove sensitive data
    user.pop('password_hash', None)
    
    # Return tokens and user info
    return User(
        access_token=access_token,
        refresh_token=refresh_token,
        email=user['email'],
        full_name=user['full_name'],
        user_name=user['user_name']
    )

def logout_user(request: RefreshToken) -> LogoutMessage:
    """Logout user by revoking refresh token"""
    db = get_db()

    result = db.table('refresh_tokens').update({
        "revoked": True
    }).eq('token', request.refresh_token).execute()

    user = db.table('refresh_tokens').select("user_id").eq('token', request.refresh_token).execute()
    user = user.data[0]

    if not result.data:
        raise ValueError("User already logged out")
    
    return LogoutMessage(
        message=f"User {user['user_id']} logged out successfully"
    )

def refresh_token(request: RefreshToken) -> Token:
    """Get new access token using stored refresh token"""
    db = get_db()

    result = db.table('refresh_tokens').select("*").eq('token', request.refresh_token).eq('revoked', False).execute()

    if not result.data:
        raise ValueError("Invalid refresh token")
    
    token_data = result.data[0]

    expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
    if expires_at < datetime.now(timezone.utc):
        raise ValueError("Refresh token expired")
    
    user_result = db.table('users').select("id, user_name").eq('id', token_data['user_id']).execute()
    if not user_result.data:
        raise ValueError("User not found")
    
    user = user_result.data[0]

    new_token_data = {
        "user_id": user['id'],
        "user_name": user['user_name'] 
    }

    new_access_token = create_access_token(new_token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=request.refresh_token,
        token_type="bearer"
    )