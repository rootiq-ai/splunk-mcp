#!/usr/bin/env python3
"""
Splunk MCP Server
A Model Context Protocol server for interacting with Splunk Enterprise/Cloud
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from splunk_client import SplunkClient
from config import SplunkConfig
from models import SearchRequest, IndexRequest, SavedSearchRequest, AppRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Splunk MCP Server")

# Global Splunk client instance
splunk_client: Optional[SplunkClient] = None


@mcp.tool()
async def search_splunk(request: SearchRequest) -> Dict[str, Any]:
    """
    Execute a Splunk search query using SPL (Search Processing Language).
    
    Args:
        request: Search parameters including query, time range, and limits
        
    Returns:
        Dictionary containing search results and metadata
    """
    global splunk_client
    
    if not splunk_client:
        raise RuntimeError("Splunk client not initialized. Please configure connection first.")
    
    try:
        logger.info(f"Executing Splunk search: {request.query}")
        
        results = await splunk_client.search(
            query=request.query,
            earliest_time=request.earliest_time,
            latest_time=request.latest_time,
            max_count=request.max_count,
            timeout=request.timeout
        )
        
        return {
            "status": "success",
            "query": request.query,
            "result_count": len(results.get("results", [])),
            "results": results.get("results", []),
            "messages": results.get("messages", []),
            "search_time": results.get("search_time"),
            "earliest_time": request.earliest_time,
            "latest_time": request.latest_time
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "query": request.query
        }


@mcp.tool()
async def list_indexes(request: IndexRequest) -> Dict[str, Any]:
    """
    List available Splunk indexes.
    
    Args:
        request: Index listing parameters including optional pattern filter
        
    Returns:
        Dictionary containing list of indexes and metadata
    """
    global splunk_client
    
    if not splunk_client:
        raise RuntimeError("Splunk client not initialized. Please configure connection first.")
    
    try:
        logger.info("Listing Splunk indexes")
        
        indexes = await splunk_client.list_indexes(pattern=request.pattern)
        
        return {
            "status": "success",
            "indexes": indexes,
            "count": len(indexes),
            "pattern": request.pattern
        }
        
    except Exception as e:
        logger.error(f"Failed to list indexes: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
async def list_saved_searches(request: SavedSearchRequest) -> Dict[str, Any]:
    """
    List or retrieve saved searches from Splunk.
    
    Args:
        request: Saved search parameters
        
    Returns:
        Dictionary containing saved searches and metadata
    """
    global splunk_client
    
    if not splunk_client:
        raise RuntimeError("Splunk client not initialized. Please configure connection first.")
    
    try:
        logger.info("Listing saved searches")
        
        saved_searches = await splunk_client.list_saved_searches(
            search_name=request.search_name,
            owner=request.owner
        )
        
        return {
            "status": "success",
            "saved_searches": saved_searches,
            "count": len(saved_searches)
        }
        
    except Exception as e:
        logger.error(f"Failed to list saved searches: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
async def list_apps(request: AppRequest) -> Dict[str, Any]:
    """
    List installed Splunk applications.
    
    Args:
        request: App listing parameters
        
    Returns:
        Dictionary containing list of applications
    """
    global splunk_client
    
    if not splunk_client:
        raise RuntimeError("Splunk client not initialized. Please configure connection first.")
    
    try:
        logger.info("Listing Splunk applications")
        
        apps = await splunk_client.list_apps(visible_only=request.visible_only)
        
        return {
            "status": "success",
            "applications": apps,
            "count": len(apps)
        }
        
    except Exception as e:
        logger.error(f"Failed to list applications: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
async def get_server_info() -> Dict[str, Any]:
    """
    Get Splunk server information and health status.
    
    Returns:
        Dictionary containing server information
    """
    global splunk_client
    
    if not splunk_client:
        raise RuntimeError("Splunk client not initialized. Please configure connection first.")
    
    try:
        logger.info("Getting Splunk server information")
        
        server_info = await splunk_client.get_server_info()
        
        return {
            "status": "success",
            "server_info": server_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get server info: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


async def initialize_splunk_client():
    """Initialize the Splunk client with configuration"""
    global splunk_client
    
    try:
        config = SplunkConfig.from_env()
        splunk_client = SplunkClient(config)
        await splunk_client.connect()
        logger.info("Splunk client initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Splunk client: {str(e)}")
        raise


async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize Splunk client
        await initialize_splunk_client()
        
        # Run the MCP server
        await mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        if splunk_client:
            await splunk_client.close()


if __name__ == "__main__":
    asyncio.run(main())
