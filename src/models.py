"""
Pydantic models for Splunk MCP Server requests and responses
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class SearchRequest(BaseModel):
    """Search request parameters"""
    query: str = Field(..., description="SPL (Search Processing Language) query")
    earliest_time: Optional[str] = Field(
        default="-24h@h", 
        description="Earliest time for search (e.g., '-24h@h', '2024-01-01T00:00:00')"
    )
    latest_time: Optional[str] = Field(
        default="now", 
        description="Latest time for search (e.g., 'now', '2024-01-01T23:59:59')"
    )
    max_count: Optional[int] = Field(
        default=100, 
        description="Maximum number of results to return",
        ge=1,
        le=10000
    )
    timeout: Optional[int] = Field(
        default=60, 
        description="Search timeout in seconds",
        ge=1,
        le=3600
    )

    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class IndexRequest(BaseModel):
    """Request to list indexes"""
    pattern: Optional[str] = Field(
        default=None, 
        description="Pattern to filter index names (e.g., 'main*', '*security*')"
    )


class SavedSearchRequest(BaseModel):
    """Request for saved searches"""
    search_name: Optional[str] = Field(
        default=None, 
        description="Name of specific saved search to retrieve"
    )
    owner: Optional[str] = Field(
        default=None, 
        description="Owner of the saved search"
    )


class AppRequest(BaseModel):
    """Request for listing applications"""
    visible_only: Optional[bool] = Field(
        default=True,
        description="Only return visible applications"
    )


class SearchResult(BaseModel):
    """Individual search result"""
    _time: Optional[str] = None
    _raw: Optional[str] = None
    host: Optional[str] = None
    source: Optional[str] = None
    sourcetype: Optional[str] = None
    index: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields from Splunk results


class SearchResponse(BaseModel):
    """Search response wrapper"""
    status: str
    query: str
    result_count: int
    results: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]
    search_time: Optional[float]
    earliest_time: str
    latest_time: str
    error: Optional[str] = None


class IndexInfo(BaseModel):
    """Index information"""
    name: str
    currentDBSizeMB: float
    maxDataSize: str
    totalEventCount: int
    disabled: bool


class IndexResponse(BaseModel):
    """Index listing response"""
    status: str
    indexes: List[IndexInfo]
    count: int
    pattern: Optional[str] = None
    error: Optional[str] = None


class SavedSearchInfo(BaseModel):
    """Saved search information"""
    name: str
    search: str
    description: str
    owner: str
    app: str
    disabled: bool
    cron_schedule: str
    next_scheduled_time: str


class SavedSearchResponse(BaseModel):
    """Saved search listing response"""
    status: str
    saved_searches: List[SavedSearchInfo]
    count: int
    error: Optional[str] = None


class AppInfo(BaseModel):
    """Application information"""
    name: str
    label: str
    description: str
    version: str
    author: str
    disabled: bool
    configured: bool


class AppResponse(BaseModel):
    """Application listing response"""
    status: str
    applications: List[AppInfo]
    count: int
    error: Optional[str] = None


class ServerInfo(BaseModel):
    """Server information"""
    version: str
    build: str
    serverName: str
    host: str
    product_type: str
    license_state: str
    mode: str
    startup_time: str


class ServerInfoResponse(BaseModel):
    """Server info response"""
    status: str
    server_info: ServerInfo
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    status: str = "error"
    error: str
    details: Optional[Dict[str, Any]] = None
