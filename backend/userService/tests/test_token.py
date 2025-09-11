import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from app.services import auth_service
from app.models.user import UserRegister, UserLogin
from app.db.database import get_db
from app.core.security import verify_token

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

def test_token_creation(test_user_data, cleanup_test_user):
    registered_user = auth_service.register_user(test_user_data)
    assert registered_user is not None
    login_data = UserLogin(
        email="test_auth@example.com",
        password="TestPassword123"
    )
    logged_in_user = auth_service.login_user(login_data)

    assert logged_in_user.access_token is not None
    assert logged_in_user.refresh_token is not None

def test_access_token_validity(test_user_data, cleanup_test_user):
    registered_user = auth_service.register_user(test_user_data)
    assert registered_user is not None
    login_data = UserLogin(
        email="test_auth@example.com",
        password="TestPassword123"
    )
    logged_in_user = auth_service.login_user(login_data)
    decoded_access_token = verify_token(logged_in_user.access_token, token_type="access")
    decoded_refresh_token = verify_token(logged_in_user.refresh_token, token_type="refresh")

    assert decoded_access_token['user_name'] == "test_user"
    assert decoded_refresh_token['user_name'] == "test_user"

def test_refresh_token_storage(test_user_data, cleanup_test_user):
    registered_user = auth_service.register_user(test_user_data)
    assert registered_user is not None
    login_data = UserLogin(
        email="test_auth@example.com",
        password="TestPassword123"
    )
    logged_in_user = auth_service.login_user(login_data)
    refresh_token = logged_in_user.refresh_token

    db = get_db()
    db_refresh_token = db.table('refresh_tokens').select("token").eq('token', refresh_token).eq('revoked', False).execute()

    assert db_refresh_token.data is not None





