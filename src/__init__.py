"""
Splunk MCP Server

A Model Context Protocol server for interacting with Splunk Enterprise/Cloud
"""

__version__ = "1.0.0"
__author__ = "Kamal Bisht"
__email__ = "kml.uvce@gmail.com"

from .config import SplunkConfig
from .splunk_client import SplunkClient
from .models import (
    SearchRequest,
    IndexRequest,
    SavedSearchRequest,
    AppRequest,
    SearchResponse,
    IndexResponse,
    SavedSearchResponse,
    AppResponse,
    ServerInfoResponse,
    ErrorResponse,
)

__all__ = [
    "SplunkConfig",
    "SplunkClient",
    "SearchRequest",
    "IndexRequest", 
    "SavedSearchRequest",
    "AppRequest",
    "SearchResponse",
    "IndexResponse",
    "SavedSearchResponse",
    "AppResponse",
    "ServerInfoResponse",
    "ErrorResponse",
]
