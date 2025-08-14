# Splunk MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with Splunk Enterprise and Splunk Cloud. This server enables AI assistants to search Splunk data, list indexes, manage saved searches, and retrieve server information through a standardized interface.

## Features

- **Search Execution**: Run SPL (Search Processing Language) queries with configurable time ranges and limits
- **Index Management**: List and filter available Splunk indexes
- **Saved Searches**: Retrieve and manage saved searches
- **Application Listing**: Browse installed Splunk applications
- **Server Information**: Get Splunk server details and health status
- **Flexible Authentication**: Support for both token-based and username/password authentication
- **Async Operations**: Built with modern Python async/await patterns
- **Type Safety**: Full Pydantic models for request/response validation

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to a Splunk Enterprise or Splunk Cloud instance
- Valid Splunk credentials (token or username/password)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/splunk-mcp.git
   cd splunk-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Splunk connection details
   ```

4. **Run the server**:
   ```bash
   python src/main.py
   ```

### Development Installation

For development with additional tools:

```bash
pip install -e ".[dev]"
```

## Configuration

The server is configured using environment variables. Copy `.env.example` to `.env` and configure:

### Required Variables

```bash
# Splunk server connection
SPLUNK_HOST=your-splunk-server.com
```

### Authentication (choose one method)

**Token-based authentication (recommended)**:
```bash
SPLUNK_TOKEN=your-splunk-token-here
```

**Username/password authentication**:
```bash
SPLUNK_USERNAME=your-username
SPLUNK_PASSWORD=your-password
```

### Optional Variables

```bash
SPLUNK_PORT=8089                    # Management port (default: 8089)
SPLUNK_SCHEME=https                 # http or https (default: https)
SPLUNK_VERIFY_SSL=true             # SSL verification (default: true)
SPLUNK_TIMEOUT=30                  # Request timeout (default: 30)
LOG_LEVEL=INFO                     # Logging level
```

## Usage

Once running, the MCP server provides the following tools:

### 1. Search Splunk Data

Execute SPL queries with configurable parameters:

```python
{
    "query": "search index=main error | head 10",
    "earliest_time": "-24h@h",
    "latest_time": "now",
    "max_count": 100,
    "timeout": 60
}
```

### 2. List Indexes

Get available Splunk indexes with optional filtering:

```python
{
    "pattern": "main*"  # Optional pattern filter
}
```

### 3. Manage Saved Searches

Retrieve saved searches by name or owner:

```python
{
    "search_name": "Security Alert",  # Optional
    "owner": "admin"                  # Optional
}
```

### 4. List Applications

Browse installed Splunk apps:

```python
{
    "visible_only": true  # Show only visible apps
}
```

### 5. Get Server Information

Retrieve Splunk server details and health status.

## API Reference

### Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | SPL search query |
| `earliest_time` | string | "-24h@h" | Search time range start |
| `latest_time` | string | "now" | Search time range end |
| `max_count` | integer | 100 | Maximum results (1-10000) |
| `timeout` | integer | 60 | Search timeout in seconds |

### Time Range Examples

- `"-24h@h"` - 24 hours ago, rounded to the hour
- `"-7d@d"` - 7 days ago, rounded to the day
- `"2024-01-01T00:00:00"` - Absolute timestamp
- `"now"` - Current time
- `"-1h"` - 1 hour ago

### SPL Query Examples

```spl
# Basic search
search index=main error

# Search with stats
index=main | stats count by host

# Time-based search
index=security earliest=-1h | where _time > relative_time(now(), "-30m")

# Complex search with transformations
index=web_logs 
| rex field=_raw "(?<status_code>\d{3})" 
| stats count by status_code 
| sort -count
```

## Authentication

### Token-Based Authentication (Recommended)

1. **Create a token in Splunk Web**:
   - Go to Settings > Tokens
   - Click "New Token"
   - Set appropriate permissions
   - Copy the generated token

2. **Configure environment**:
   ```bash
   SPLUNK_TOKEN=your-token-here
   ```

### Username/Password Authentication

```bash
SPLUNK_USERNAME=your-username
SPLUNK_PASSWORD=your-password
```

**Note**: Token authentication is more secure and is the recommended approach for production deployments.

## Error Handling

The server provides detailed error responses:

```json
{
    "status": "error",
    "error": "Authentication failed",
    "details": {
        "code": 401,
        "message": "Invalid credentials"
    }
}
```

Common error scenarios:
- **Authentication failures**: Invalid credentials or expired tokens
- **Query syntax errors**: Malformed SPL queries
- **Permission issues**: Insufficient access to indexes or searches
- **Timeout errors**: Long-running searches exceeding timeout limits
- **Connection issues**: Network problems or Splunk server unavailability

## Security Considerations

- **Use HTTPS**: Always use encrypted connections in production
- **Secure credentials**: Store tokens and passwords securely
- **Limit permissions**: Use principle of least privilege for Splunk accounts
- **Network security**: Restrict network access to Splunk management ports
- **Token rotation**: Regularly rotate authentication tokens

## Development

### Project Structure

```
splunk-mcp/
├── src/
│   ├── main.py              # MCP server entry point
│   ├── splunk_client.py     # Splunk REST API client
│   ├── config.py            # Configuration management
│   └── models.py            # Pydantic data models
├── tests/                   # Test files
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "src/main.py"]
```

Build and run:

```bash
docker build -t splunk-mcp .
docker run --env-file .env splunk-mcp
```

### Production Considerations

- Use a process manager like `supervisor` or `systemd`
- Configure proper logging and monitoring
- Set up health checks
- Use environment-specific configuration
- Implement proper secret management

## Troubleshooting

### Common Issues

1. **Connection refused**:
   - Check Splunk server is running
   - Verify host and port settings
   - Check network connectivity

2. **Authentication errors**:
   - Verify credentials are correct
   - Check token hasn't expired
   - Ensure user has necessary permissions

3. **Search timeouts**:
   - Reduce search time range
   - Optimize SPL query
   - Increase timeout setting

4. **SSL errors**:
   - Check certificate validity
   - Set `SPLUNK_VERIFY_SSL=false` for testing (not recommended for production)

### Enabling Debug Logging

```bash
LOG_LEVEL=DEBUG python src/main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/splunk-mcp/issues)
- **Documentation**: [Project Wiki](https://github.com/yourusername/splunk-mcp/wiki)
- **Splunk Documentation**: [Splunk REST API Reference](https://docs.splunk.com/Documentation/Splunk/latest/RESTREF)

## Changelog

### v1.0.0
- Initial release
- Basic search functionality
- Token and username/password authentication
- Index and saved search management
- Application listing
- Server information retrieval
