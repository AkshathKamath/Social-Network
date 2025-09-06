# tests/test_db_connection.py
import pytest
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

@pytest.fixture
def supabase_client() -> Client:
    """Fixture to create and return Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Check credentials exist
    assert url is not None, "SUPABASE_URL not found in environment"
    assert key is not None, "SUPABASE_SERVICE_KEY not found in environment"
    
    # Create and return client
    client = create_client(url, key)
    return client

def test_database_connection(supabase_client):
    """Test that we can connect to Supabase database"""
    assert supabase_client is not None, "Failed to create Supabase client"

def test_users_table_exists(supabase_client):
    """Test that users table exists and is accessible"""
    try:
        result = supabase_client.table('users').select("*").limit(1).execute()
        assert result is not None
    except Exception as e:
        pytest.fail(f"Failed to access users table: {e}")