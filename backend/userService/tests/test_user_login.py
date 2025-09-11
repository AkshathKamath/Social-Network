import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from app.services import auth_service
from app.models.user import UserRegister, UserLogin
from app.db.database import get_db



@pytest.fixture
def test_user_data():
    """Fixture for test user data"""
    return UserRegister(
        email="test_auth@example.com",
        password="TestPassword123",
        full_name="Test User",
        user_name="test_user",
        date_of_birth=date(1990, 1, 1)
    )

@pytest.fixture
def cleanup_test_user():
    """Cleanup test users after tests"""
    yield
    # Cleanup after test
    db = get_db()
    db.table('users').delete().eq('email', 'test_auth@example.com').execute()

def test_login_successful(test_user_data, cleanup_test_user):
    """Test successful login with correct credentials"""
    # First, register the user
    registered_user = auth_service.register_user(test_user_data)
    assert registered_user is not None
    
    # Now test login with correct credentials
    login_data = UserLogin(
        email="test_auth@example.com",
        password="TestPassword123"
    )
    
    # Attempt login
    logged_in_user = auth_service.login_user(login_data)
    
    # Assertions for successful login
    assert logged_in_user is not None
    assert logged_in_user.email == "test_auth@example.com"
    assert logged_in_user.full_name == "Test User"
    assert 'password_hash' not in logged_in_user  # Password should not be returned
    assert logged_in_user.user_name == "test_user"

def test_login_wrong_password(test_user_data, cleanup_test_user):
    """Test login failure with wrong password"""
    # First, register the user
    registered_user = auth_service.register_user(test_user_data)
    assert registered_user is not None
    
    # Try login with wrong password
    login_data = UserLogin(
        email="test_auth@example.com",
        password="WrongPassword123"  # Wrong password
    )
    
    # Attempt login
    result = auth_service.login_user(login_data)
    
    # Should return None for failed authentication
    assert result is None

def test_login_nonexistent_user():
    """Test login failure with non-existent email"""
    # Try login with email that doesn't exist
    login_data = UserLogin(
        email="nonexistent@example.com",
        password="SomePassword123"
    )
    
    # Attempt login
    result = auth_service.login_user(login_data)
    
    # Should return None for non-existent user
    assert result is None