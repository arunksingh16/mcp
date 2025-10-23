import httpx
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
from fastmcp import FastMCP
from fastapi.responses import JSONResponse

mcp = FastMCP("AWS News MCP")

# Access the underlying FastAPI app to add health endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "aws-news-mcp-server"})

async def fetch_aws_news(
    topic: str,
    news_type: str = "all",
    include_regional_expansions: bool = False,
    limit: int = 40,
    since_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch AWS news articles based on the provided parameters.

    Args:
        topic: The AWS topic/service to search for
        news_type: Type of news to fetch ('all', 'news', 'blogs')
        include_regional_expansions: Whether to include regional expansion news
        limit: Maximum number of results to return
        since_date: Optional ISO 8601 date to filter results

    Returns:
        List of news articles
    """
    base_url = "https://api.aws-news.com/articles"

    # Build query parameters
    params = {
        "page_size": limit,
        "hide_regional_expansions": not include_regional_expansions,
        "search": topic
    }

    # Add article type filter if specified
    if news_type.lower() == "news":
        params["article_type"] = "news"
    elif news_type.lower() == "blogs" or news_type.lower() == "blog":
        params["article_type"] = "blog"

    # Add date filter if provided
    if since_date:
        try:
            # Validate the date format
            datetime.fromisoformat(since_date.replace('Z', '+00:00'))
            params["since"] = since_date
        except ValueError:
            raise ValueError(
                "Invalid date format. Please use ISO 8601 format (e.g., 2025-05-01T00:00:00Z)")

    # Construct the URL with query parameters
    url = f"{base_url}?{urlencode(params)}"

    # Make the request
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        # Parse and return the JSON response
        data = response.json()
        return data


@mcp.tool(
    description="""
Returns a list of AWS news articles with announcements of new products, services, and capabilities for the specified AWS topic/service.

You can filter on news type which is news or blogs. By default, returns both news and blogs.

You can optionally ask for regional expansion news (defaults to false).

Optionally, specify a "since" date in ISO 8601 format by which to filter the results.

Examples:
- To get all news about Amazon S3: use topic="s3"
- To get only blog posts about Amazon EC2: use topic="ec2", news_type="blogs"
- To get news about Lambda since January 2025: use topic="lambda", since_date="2025-01-01T00:00:00Z"
- To get regional expansion news for DynamoDB: use topic="dynamodb", include_regional_expansions=true

Use this tool when:
1. The user asks about recent AWS announcements for a specific service
2. The user wants to know about new features or capabilities in AWS services
3. The user is looking for AWS blog posts about specific topics
4. The user wants to stay updated on AWS service expansions to new regions
"""
)
async def get_aws_news(
    topic: str,
    news_type: str = "all",
    include_regional_expansions: bool = False,
    number_of_results: int = 40,
    since_date: Optional[str] = None,
) -> str:
    """
    Get AWS news articles for a specific topic or service.

    Args:
        topic: AWS topic or service to search for (e.g., 's3', 'lambda', 'ec2')
        news_type: Type of news to return (all, news, or blogs)
        include_regional_expansions: Whether to include regional expansion news
        number_of_results: Maximum number of results to return
        since_date: Optional ISO 8601 date to filter results (e.g., '2025-01-01T00:00:00Z')

    Returns:
        JSON string containing the news articles
    """
    try:
        news_articles = await fetch_aws_news(
            topic=topic,
            news_type=news_type,
            include_regional_expansions=include_regional_expansions,
            limit=number_of_results,
            since_date=since_date
        )

        # Format the response
        result = {
            "topic": topic,
            "news_type": news_type,
            "include_regional_expansions": include_regional_expansions,
            "articles": news_articles
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching AWS news: {str(e)}"


@mcp.prompt
def aws_latest_prompt(topics: str, days_ago: int = 90) -> str:
    """Get the latest news and blogs from AWS on a list of subjects"""
    return f"Tell me the latest AWS news and blogs for {topics} over the past {days_ago} days."

@mcp.prompt
def aws_news_prompt(topics: str, days_ago: int = 90) -> str:
    """Get the latest AWS news announcements"""
    return f"Tell me the latest AWS news of type news for {topics} over the past {days_ago} days."

@mcp.prompt
def aws_blogs_prompt(topics: str, days_ago: int = 90) -> str:
    """Get the latest AWS blog posts"""
    return f"Tell me the latest AWS blog posts for {topics} over the past {days_ago} days."

if __name__ == "__main__":
    mcp.run(transport="http", port=8000, host="0.0.0.0")