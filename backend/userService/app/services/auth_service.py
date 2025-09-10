from app.db.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import UserRegister, UserLogin
from app.models.token import RefreshToken
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone

def register_user(user_data: UserRegister) -> Dict:
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
        user.pop('password_hash', None)  # Don't return password hash
        return user
    
    raise Exception("Failed to create user")

def login_user(login_data: UserLogin) -> Optional[Dict]:
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
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

def logout_user(request: RefreshToken):
    """Logout user by revoking refresh token"""
    db = get_db()

    result = db.table('refresh_tokens').update({
        "revoked": True
    }).eq('token', request.refresh_token).execute()

    user = db.table('refresh_tokens').select("user_id").eq('token', request.refresh_token).execute()
    user = user.data[0]

    if not result.data:
        raise ValueError("User already logged out")
    
    return {
        "user_id": user
    }
    