import pytest
import httpx
from typing import Generator
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

BASE_URL = os.getenv('USER_SERVICE_URL')
TEST_REGISTER_USER = {
    "email": "integration_test@example.com",
    "password": "TestPassword123",
    "full_name": "Integration Test User",
    "user_name": "integration_test_user",
    "date_of_birth": "1990-01-01"
}
TEST_LOGIN_USER = {
    "email": "integration_test@example.com",
    "password": "TestPassword123"
}

supabase_client: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

@pytest.fixture
def client() -> Generator[httpx.Client, None, None]:
    """Create HTTP client for testing"""
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_test_user():
    """Ensure clean test state before and after each test"""
    # Pre-cleanup
    try:
        supabase_client.table('users').delete().eq('email', TEST_REGISTER_USER["email"]).execute()
    except Exception:
        pass  # Ignore if user doesn't exist
    
    yield
    
    # Post-cleanup
    try:
        supabase_client.table('users').delete().eq('email', TEST_REGISTER_USER["email"]).execute()
    except Exception as e:
        print(f"Cleanup warning: {e}")

def test_register_new_user(client):
    response = client.post("auth/register", json=TEST_REGISTER_USER)
    
    assert response.status_code in [200, 201]  # Accept both
    data = response.json()
    
    # Verify response structure
    assert data["email"] == TEST_REGISTER_USER["email"]
    assert data["full_name"] == TEST_REGISTER_USER["full_name"]
    assert data["user_name"] == TEST_REGISTER_USER["user_name"]

def test_login_user(client):
    client.post("auth/register", json=TEST_REGISTER_USER)
    response = client.post("auth/login", json=TEST_LOGIN_USER)
    assert response.status_code in [200, 201]  # Accept both
    data = response.json()

    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["email"] == TEST_REGISTER_USER["email"]
    assert data["full_name"] == TEST_REGISTER_USER["full_name"]
    assert data["user_name"] == TEST_REGISTER_USER["user_name"]