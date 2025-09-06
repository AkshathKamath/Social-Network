from app.db.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import UserRegister, UserLogin
from typing import Optional, Dict

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
    
    # Remove sensitive data before returning
    user.pop('password_hash', None)
    return user