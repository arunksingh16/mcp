from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from fastmcp import FastMCP, Context
import requests
import httpx
import os
from typing import Dict, Any, List

# API_URL
API_URL = os.environ.get("API_URL")
# Get API key from environment variable, with a fallback for local development
API_KEY = os.environ.get("API_KEY")


mcp = FastMCP(
    name="CopilotDataAnalyzer",
    instructions="""
    This is a Microsoft Copilot usage analytics server that provides comprehensive data analysis capabilities.
    
    KEY CAPABILITIES:
    - Retrieve real-time Copilot usage statistics and metrics
    - Analyze user adoption patterns and trends
    - Generate usage reports and insights
    - Monitor application performance and feature utilization
    
    WHEN TO USE THIS SERVER:
    - User asks about "Copilot usage", "Microsoft Copilot data", "Copilot analytics"
    - Questions about user adoption, feature usage, or performance metrics
    - Requests for usage reports, dashboards, or trend analysis
    - Any inquiry related to Copilot statistics or insights
    
    AVAILABLE TOOLS:
    - get_copilot_usage(): Fetches current usage data with detailed metrics
    - get_usage_summary(): Returns condensed summary of key metrics
    - get_usage_trends(): Analyzes trends over time periods
    - analyze_user_adoption(): Provides user adoption insights
    
    Always use get_copilot_usage() as the primary data source and supplement with other tools as needed.
    """
)

@mcp.tool()
async def get_usage():
    """
    Retrieve comprehensive Microsoft Copilot usage data and analytics.
    
    Returns:
        Json containing usage statistics, user metrics, feature adoption,
        and performance data from the Copilot platform.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(API_URL, headers={
            'x-api-key': API_KEY,
            'Content-Type': 'application/json'
        }, timeout=10)
        return resp.json()


# Resource for version information
@mcp.resource("config://version")
async def get_version() -> str:
    """Returns the current version of the application."""
    return "0.0.1"

# Resource returning JSON data (dict is auto-serialized)
@mcp.resource("copilot://usage/live")
async def get_live_usage_data() -> Dict[str, Any]:
    """
    Provides real-time Microsoft Copilot usage data directly from the API.
    This resource is automatically refreshed and contains the most current statistics.
    """
    try:
        headers = {
            'x-api-key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Parse JSON response instead of returning raw text
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch config: {str(e)}",
            "status": "error"
        }


@mcp.resource("data://config/cached")
def get_cached_config() -> Dict[str, Any]:
    """Provides cached configuration data (mock implementation)."""
    return {
        "app_name": "Demo App",
        "version": "0.0.1",
        "features": ["api_access", "caching", "monitoring"],
        "last_updated": "2025-06-07T10:00:00Z"
    }

@mcp.prompt
def summarize_request(text: str) -> str:
    """Generate a prompt asking for a summary."""
    return f"Please summarize the following text:\n\n{text}"



if __name__ == "__main__":
    # Get server mode from environment variable, default to "sse"
    # Valid values: "sse" or "studio"
    server_mode = os.environ.get("MCP_SERVER_MODE", "sse").lower()
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Get host from environment variable or use default
    host = os.environ.get("HOST", "0.0.0.0")


    # Configure and run server based on mode
    if server_mode == "stdio":
        # Run in studio mode
        print("Starting server in studio mode")
        mcp.run(transport="stdio")
    else:
        # Run in SSE mode
        print(f"Starting server in SSE mode on {host}:{port}")
        mcp.run(
            transport="streamable-http", 
            host=host,
            port=port,         
            path="/mcp",
            log_level="debug"
        )
