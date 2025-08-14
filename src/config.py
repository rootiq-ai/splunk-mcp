"""
Configuration management for Splunk MCP Server
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SplunkConfig:
    """Splunk connection configuration"""
    
    host: str
    port: int = 8089
    scheme: str = "https"
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "SplunkConfig":
        """Create configuration from environment variables"""
        
        # Required host
        host = os.getenv("SPLUNK_HOST")
        if not host:
            raise ValueError("SPLUNK_HOST environment variable is required")
        
        # Optional port (default: 8089)
        port = int(os.getenv("SPLUNK_PORT", "8089"))
        
        # Optional scheme (default: https)
        scheme = os.getenv("SPLUNK_SCHEME", "https")
        
        # Authentication - either token or username/password
        token = os.getenv("SPLUNK_TOKEN")
        username = os.getenv("SPLUNK_USERNAME")
        password = os.getenv("SPLUNK_PASSWORD")
        
        if not token and not (username and password):
            raise ValueError(
                "Either SPLUNK_TOKEN or both SPLUNK_USERNAME and SPLUNK_PASSWORD "
                "environment variables are required"
            )
        
        # SSL verification (default: True)
        verify_ssl = os.getenv("SPLUNK_VERIFY_SSL", "true").lower() in ("true", "1", "yes")
        
        # Timeout (default: 30 seconds)
        timeout = int(os.getenv("SPLUNK_TIMEOUT", "30"))
        
        return cls(
            host=host,
            port=port,
            scheme=scheme,
            username=username,
            password=password,
            token=token,
            verify_ssl=verify_ssl,
            timeout=timeout
        )
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.token and not (self.username and self.password):
            raise ValueError("Either token or username/password must be provided")
        
        if self.scheme not in ("http", "https"):
            raise ValueError("Scheme must be either 'http' or 'https'")
        
        if self.port < 1 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for Splunk API"""
        return f"{self.scheme}://{self.host}:{self.port}"
    
    def __repr__(self) -> str:
        """String representation without sensitive data"""
        return (
            f"SplunkConfig("
            f"host='{self.host}', "
            f"port={self.port}, "
            f"scheme='{self.scheme}', "
            f"username={'***' if self.username else None}, "
            f"password={'***' if self.password else None}, "
            f"token={'***' if self.token else None}, "
            f"verify_ssl={self.verify_ssl}, "
            f"timeout={self.timeout}"
            f")"
        )
