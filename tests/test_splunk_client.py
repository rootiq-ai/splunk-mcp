"""
Tests for Splunk Client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession

from src.config import SplunkConfig
from src.splunk_client import SplunkClient


@pytest.fixture
def mock_config():
    """Create a mock Splunk configuration"""
    return SplunkConfig(
        host="test-splunk.com",
        port=8089,
        scheme="https",
        token="test-token",
        verify_ssl=False,
        timeout=30
    )


@pytest.fixture
def mock_config_userpass():
    """Create a mock Splunk configuration with username/password"""
    return SplunkConfig(
        host="test-splunk.com",
        port=8089,
        scheme="https",
        username="testuser",
        password="testpass",
        verify_ssl=False,
        timeout=30
    )


@pytest.fixture
async def splunk_client(mock_config):
    """Create a Splunk client for testing"""
    client = SplunkClient(mock_config)
    yield client
    if client.session:
        await client.close()


class TestSplunkClient:
    """Test cases for SplunkClient"""

    @pytest.mark.asyncio
    async def test_init(self, mock_config):
        """Test client initialization"""
        client = SplunkClient(mock_config)
        assert client.config == mock_config
        assert client.session is None
        assert client.session_key is None
        assert client.base_url == "https://test-splunk.com:8089"

    @pytest.mark.asyncio
    async def test_connect_token_auth(self, mock_config):
        """Test connection with token authentication"""
        client = SplunkClient(mock_config)
        
        # Mock the HTTP session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.headers = {}
            mock_session_class.return_value = mock_session
            
            await client.connect()
            
            assert client.session is not None
            assert "Authorization" in mock_session.headers
            assert mock_session.headers["Authorization"] == "Bearer test-token"

    @pytest.mark.asyncio
    async def test_connect_userpass_auth(self, mock_config_userpass):
        """Test connection with username/password authentication"""
        client = SplunkClient(mock_config_userpass)
        
        # Mock successful authentication response
        mock_auth_response = AsyncMock()
        mock_auth_response.status = 200
        mock_auth_response.json = AsyncMock(return_value={"sessionKey": "test-session-key"})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(return_value=mock_auth_response)
            mock_session.headers = {}
            mock_session_class.return_value = mock_session
            
            await client.connect()
            
            assert client.session is not None
            assert client.session_key == "test-session-key"
            assert "Authorization" in mock_session.headers
            assert mock_session.headers["Authorization"] == "Splunk test-session-key"

    @pytest.mark.asyncio
    async def test_search_success(self, splunk_client):
        """Test successful search execution"""
        # Mock the search workflow
        job_response = {"sid": "test-search-id"}
        status_response = {
            "entry": [{
                "content": {"dispatchState": "DONE"}
            }]
        }
        results_response = {
            "results": [
                {"_time": "2024-01-01T00:00:00", "_raw": "test log entry"}
            ],
            "messages": []
        }
        
        with patch.object(splunk_client, '_make_request') as mock_request:
            mock_request.side_effect = [
                job_response,      # Create job
                status_response,   # Check status
                results_response,  # Get results
                {}                 # Delete job
            ]
            
            result = await splunk_client.search(
                query="search index=main",
                earliest_time="-1h",
                latest_time="now",
                max_count=10
            )
            
            assert "results" in result
            assert len(result["results"]) == 1
            assert result["results"][0]["_raw"] == "test log entry"
            assert "search_time" in result

    @pytest.mark.asyncio
    async def test_list_indexes(self, splunk_client):
        """Test listing indexes"""
        mock_response = {
            "entry": [
                {
                    "name": "main",
                    "content": {
                        "currentDBSizeMB": 1024.5,
                        "maxDataSize": "auto",
                        "totalEventCount": 100000,
                        "disabled": False
                    }
                },
                {
                    "name": "security",
                    "content": {
                        "currentDBSizeMB": 512.25,
                        "maxDataSize": "1GB",
                        "totalEventCount": 50000,
                        "disabled": False
                    }
                }
            ]
        }
        
        with patch.object(splunk_client, '_make_request', return_value=mock_response):
            indexes = await splunk_client.list_indexes()
            
            assert len(indexes) == 2
            assert indexes[0]["name"] == "main"
            assert indexes[0]["currentDBSizeMB"] == 1024.5
            assert indexes[1]["name"] == "security"

    @pytest.mark.asyncio
    async def test_list_indexes_with_pattern(self, splunk_client):
        """Test listing indexes with pattern filter"""
        mock_response = {
            "entry": [
                {"name": "main", "content": {}},
                {"name": "security", "content": {}},
                {"name": "web_logs", "content": {}}
            ]
        }
        
        with patch.object(splunk_client, '_make_request', return_value=mock_response):
            indexes = await splunk_client.list_indexes(pattern="main*")
            
            # Should only return indexes matching the pattern
            assert len(indexes) == 1
            assert indexes[0]["name"] == "main"

    @pytest.mark.asyncio
    async def test_list_saved_searches(self, splunk_client):
        """Test listing saved searches"""
        mock_response = {
            "entry": [
                {
                    "name": "Security Alerts",
                    "author": "admin",
                    "content": {
                        "search": "index=security error",
                        "description": "Security error monitoring",
                        "disabled": False,
                        "cron_schedule": "0 */6 * * *",
                        "next_scheduled_time": "2024-01-01T06:00:00"
                    },
                    "acl": {"app": "search"}
                }
            ]
        }
        
        with patch.object(splunk_client, '_make_request', return_value=mock_response):
            searches = await splunk_client.list_saved_searches()
            
            assert len(searches) == 1
            assert searches[0]["name"] == "Security Alerts"
            assert searches[0]["search"] == "index=security error"
            assert searches[0]["owner"] == "admin"

    @pytest.mark.asyncio
    async def test_get_server_info(self, splunk_client):
        """Test getting server information"""
        mock_response = {
            "entry": [{
                "content": {
                    "version": "9.0.0",
                    "build": "12345",
                    "serverName": "test-splunk",
                    "host": "test-splunk.com",
                    "product_type": "enterprise",
                    "license_state": "OK",
                    "mode": "normal",
                    "startup_time": "2024-01-01T00:00:00"
                }
            }]
        }
        
        with patch.object(splunk_client, '_make_request', return_value=mock_response):
            server_info = await splunk_client.get_server_info()
            
            assert server_info["version"] == "9.0.0"
            assert server_info["serverName"] == "test-splunk"
            assert server_info["product_type"] == "enterprise"

    @pytest.mark.asyncio
    async def test_authentication_error(self, mock_config):
        """Test authentication failure"""
        client = SplunkClient(mock_config)
        
        # Mock failed authentication
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.headers = {}
            mock_session_class.return_value = mock_session
            
            with pytest.raises(Exception, match="Token authentication failed"):
                await client.connect()

    @pytest.mark.asyncio
    async def test_search_timeout(self, splunk_client):
        """Test search timeout handling"""
        job_response = {"sid": "test-search-id"}
        # Mock status that never completes
        status_response = {
            "entry": [{
                "content": {"dispatchState": "RUNNING"}
            }]
        }
        
        with patch.object(splunk_client, '_make_request') as mock_request:
            mock_request.side_effect = [
                job_response,      # Create job
                status_response,   # Check status (always running)
            ]
            
            with pytest.raises(Exception, match="Search timeout"):
                await splunk_client.search(
                    query="search index=main",
                    timeout=1  # Very short timeout
                )


class TestSplunkConfig:
    """Test cases for SplunkConfig"""

    def test_config_from_env_token(self, monkeypatch):
        """Test configuration from environment variables with token"""
        monkeypatch.setenv("SPLUNK_HOST", "test.splunk.com")
        monkeypatch.setenv("SPLUNK_TOKEN", "test-token")
        monkeypatch.setenv("SPLUNK_PORT", "8089")
        monkeypatch.setenv("SPLUNK_SCHEME", "https")
        
        config = SplunkConfig.from_env()
        
        assert config.host == "test.splunk.com"
        assert config.token == "test-token"
        assert config.port == 8089
        assert config.scheme == "https"

    def test_config_from_env_userpass(self, monkeypatch):
        """Test configuration from environment variables with username/password"""
        monkeypatch.setenv("SPLUNK_HOST", "test.splunk.com")
        monkeypatch.setenv("SPLUNK_USERNAME", "testuser")
        monkeypatch.setenv("SPLUNK_PASSWORD", "testpass")
        
        config = SplunkConfig.from_env()
        
        assert config.host == "test.splunk.com"
        assert config.username == "testuser"
        assert config.password == "testpass"

    def test_config_missing_host(self, monkeypatch):
        """Test configuration with missing host"""
        monkeypatch.delenv("SPLUNK_HOST", raising=False)
        
        with pytest.raises(ValueError, match="SPLUNK_HOST environment variable is required"):
            SplunkConfig.from_env()

    def test_config_missing_auth(self, monkeypatch):
        """Test configuration with missing authentication"""
        monkeypatch.setenv("SPLUNK_HOST", "test.splunk.com")
        monkeypatch.delenv("SPLUNK_TOKEN", raising=False)
        monkeypatch.delenv("SPLUNK_USERNAME", raising=False)
        monkeypatch.delenv("SPLUNK_PASSWORD", raising=False)
        
        with pytest.raises(ValueError, match="Either SPLUNK_TOKEN or both SPLUNK_USERNAME"):
            SplunkConfig.from_env()
