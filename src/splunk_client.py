"""
Splunk API Client
Handles authentication and API interactions with Splunk Enterprise/Cloud
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import aiohttp
import xmltodict

from config import SplunkConfig

logger = logging.getLogger(__name__)


class SplunkClient:
    """Async Splunk REST API client"""
    
    def __init__(self, config: SplunkConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_key: Optional[str] = None
        self.base_url = f"{config.scheme}://{config.host}:{config.port}"
        
    async def connect(self):
        """Establish connection and authenticate with Splunk"""
        if self.session:
            await self.session.close()
            
        # Create SSL context for HTTPS
        ssl_context = None
        if self.config.scheme == "https":
            import ssl
            ssl_context = ssl.create_default_context()
            if not self.config.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create session with appropriate settings
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Splunk-MCP-Client/1.0"}
        )
        
        await self._authenticate()
        
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _authenticate(self):
        """Authenticate with Splunk and get session key"""
        auth_url = urljoin(self.base_url, "/services/auth/login")
        
        # Prepare authentication data
        if self.config.token:
            # Token-based authentication
            headers = {"Authorization": f"Bearer {self.config.token}"}
            self.session.headers.update(headers)
            
            # Test the token by making a simple API call
            test_url = urljoin(self.base_url, "/services/server/info")
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    logger.info("Token authentication successful")
                    return
                else:
                    raise Exception(f"Token authentication failed: {response.status}")
                    
        elif self.config.username and self.config.password:
            # Username/password authentication
            auth_data = {
                "username": self.config.username,
                "password": self.config.password,
                "output_mode": "json"
            }
            
            async with self.session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.session_key = result["sessionKey"]
                    
                    # Update session headers with session key
                    self.session.headers.update({
                        "Authorization": f"Splunk {self.session_key}"
                    })
                    
                    logger.info("Username/password authentication successful")
                else:
                    error_text = await response.text()
                    raise Exception(f"Authentication failed: {response.status} - {error_text}")
        else:
            raise Exception("No authentication method provided. Use either token or username/password.")
            
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Splunk API"""
        if not self.session:
            raise Exception("Client not connected. Call connect() first.")
            
        url = urljoin(self.base_url, endpoint)
        
        # Set default output mode to JSON
        if "params" not in kwargs:
            kwargs["params"] = {}
        if "output_mode" not in kwargs["params"]:
            kwargs["params"]["output_mode"] = "json"
            
        async with self.session.request(method, url, **kwargs) as response:
            if response.status in (200, 201):
                content_type = response.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    return await response.json()
                elif "text/xml" in content_type or "application/xml" in content_type:
                    xml_content = await response.text()
                    return xmltodict.parse(xml_content)
                else:
                    return {"text": await response.text()}
            else:
                error_text = await response.text()
                raise Exception(f"API request failed: {response.status} - {error_text}")
                
    async def search(
        self,
        query: str,
        earliest_time: str = "-24h@h",
        latest_time: str = "now",
        max_count: int = 100,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Execute a search query"""
        
        # Create search job
        search_params = {
            "search": query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "max_count": max_count,
            "output_mode": "json"
        }
        
        job_response = await self._make_request(
            "POST",
            "/services/search/jobs",
            data=search_params
        )
        
        search_id = job_response["sid"]
        logger.info(f"Created search job: {search_id}")
        
        # Wait for search to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            job_status = await self._make_request(
                "GET",
                f"/services/search/jobs/{search_id}"
            )
            
            entry = job_status["entry"][0] if "entry" in job_status else {}
            content = entry.get("content", {})
            
            if content.get("dispatchState") == "DONE":
                break
            elif content.get("dispatchState") == "FAILED":
                raise Exception(f"Search failed: {content.get('messages', 'Unknown error')}")
                
            await asyncio.sleep(1)
        else:
            raise Exception(f"Search timeout after {timeout} seconds")
            
        # Get search results
        results_response = await self._make_request(
            "GET",
            f"/services/search/jobs/{search_id}/results"
        )
        
        # Clean up search job
        await self._make_request("DELETE", f"/services/search/jobs/{search_id}")
        
        return {
            "results": results_response.get("results", []),
            "messages": results_response.get("messages", []),
            "search_time": time.time() - start_time
        }
        
    async def list_indexes(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available indexes"""
        response = await self._make_request("GET", "/services/data/indexes")
        
        indexes = []
        for entry in response.get("entry", []):
            index_name = entry.get("name", "")
            
            # Apply pattern filter if provided
            if pattern:
                import fnmatch
                if not fnmatch.fnmatch(index_name, pattern):
                    continue
                    
            content = entry.get("content", {})
            indexes.append({
                "name": index_name,
                "currentDBSizeMB": content.get("currentDBSizeMB", 0),
                "maxDataSize": content.get("maxDataSize", "auto"),
                "totalEventCount": content.get("totalEventCount", 0),
                "disabled": content.get("disabled", False)
            })
            
        return sorted(indexes, key=lambda x: x["name"])
        
    async def list_saved_searches(
        self,
        search_name: Optional[str] = None,
        owner: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List saved searches"""
        endpoint = "/services/saved/searches"
        params = {}
        
        if owner:
            params["owner"] = owner
            
        response = await self._make_request("GET", endpoint, params=params)
        
        saved_searches = []
        for entry in response.get("entry", []):
            name = entry.get("name", "")
            
            # Filter by search name if provided
            if search_name and search_name.lower() not in name.lower():
                continue
                
            content = entry.get("content", {})
            saved_searches.append({
                "name": name,
                "search": content.get("search", ""),
                "description": content.get("description", ""),
                "owner": entry.get("author", ""),
                "app": entry.get("acl", {}).get("app", ""),
                "disabled": content.get("disabled", False),
                "cron_schedule": content.get("cron_schedule", ""),
                "next_scheduled_time": content.get("next_scheduled_time", "")
            })
            
        return sorted(saved_searches, key=lambda x: x["name"])
        
    async def list_apps(self, visible_only: bool = True) -> List[Dict[str, Any]]:
        """List installed applications"""
        response = await self._make_request("GET", "/services/apps/local")
        
        apps = []
        for entry in response.get("entry", []):
            content = entry.get("content", {})
            
            # Filter visible apps only if requested
            if visible_only and content.get("visible", True) is False:
                continue
                
            apps.append({
                "name": entry.get("name", ""),
                "label": content.get("label", ""),
                "description": content.get("description", ""),
                "version": content.get("version", ""),
                "author": entry.get("author", ""),
                "disabled": content.get("disabled", False),
                "configured": content.get("configured", False)
            })
            
        return sorted(apps, key=lambda x: x["name"])
        
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        response = await self._make_request("GET", "/services/server/info")
        
        if "entry" in response and len(response["entry"]) > 0:
            content = response["entry"][0].get("content", {})
            return {
                "version": content.get("version", ""),
                "build": content.get("build", ""),
                "serverName": content.get("serverName", ""),
                "host": content.get("host", ""),
                "product_type": content.get("product_type", ""),
                "license_state": content.get("license_state", ""),
                "mode": content.get("mode", ""),
                "startup_time": content.get("startup_time", "")
            }
        else:
            return {}
