import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
import boto3
from botocore.exceptions import ClientError
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    PromptMessage,
    Prompt,
)
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

class DynamoDBMCPServer:
    def __init__(self):
        self.server = Server("dynamodb-mcp-server")
        self.dynamodb = None
        self.table_names = []
        # Store handler functions for direct access
        self.handlers = {}
        self._setup_dynamodb()
        self._setup_handlers()
    
    def _setup_dynamodb(self):
        """Initialize DynamoDB client and discover tables"""
        try:
            self.dynamodb = boto3.resource('dynamodb', 
                                         region_name=os.getenv('AWS_REGION', 'us-east-1'))
            
            # Get list of available tables
            client = boto3.client('dynamodb', 
                                region_name=os.getenv('AWS_REGION', 'us-east-1'))
            response = client.list_tables()
            self.table_names = response['TableNames']
            
            logger.info(f"Connected to DynamoDB. Found tables: {self.table_names}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB: {e}")
            self.table_names = []
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available DynamoDB tables as resources"""
            resources = []
            for table_name in self.table_names:
                resources.append(
                    Resource(
                        uri=f"dynamodb://table/{table_name}",
                        name=f"DynamoDB Table: {table_name}",
                        description=f"DynamoDB table '{table_name}' with full table metadata and sample data",
                        mimeType="application/json"
                    )
                )
            return ListResourcesResult(resources=resources)
        
        # Store the handler function for direct access
        self.handlers['list_resources'] = list_resources
        
        @self.server.read_resource()
        async def read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            """Read table schema and sample data"""
            try:
                # Parse table name from URI
                if not request.uri.startswith("dynamodb://table/"):
                    raise ValueError("Invalid DynamoDB URI format")
                
                table_name = request.uri.replace("dynamodb://table/", "")
                
                if table_name not in self.table_names:
                    raise ValueError(f"Table {table_name} not found")
                
                table = self.dynamodb.Table(table_name)
                
                # Get table metadata
                table_info = {
                    "table_name": table_name,
                    "table_status": table.table_status,
                    "key_schema": table.key_schema,
                    "attribute_definitions": table.attribute_definitions,
                    "item_count": table.item_count,
                    "table_size_bytes": table.table_size_bytes,
                }
                
                # Get sample data (first 10 items)
                try:
                    response = table.scan(Limit=10)
                    sample_items = response.get('Items', [])
                    table_info["sample_data"] = sample_items
                except Exception as e:
                    logger.warning(f"Could not fetch sample data for {table_name}: {e}")
                    table_info["sample_data"] = []
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(table_info, cls=DecimalEncoder, indent=2)
                        )
                    ]
                )
                
            except Exception as e:
                logger.error(f"Error reading resource: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Error reading table: {str(e)}"
                        )
                    ]
                )
        
        # Store the handler function for direct access
        self.handlers['read_resource'] = read_resource
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available DynamoDB tools"""
            tools = [
                Tool(
                    name="scan_table",
                    description="Scan a DynamoDB table with optional filters and limits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the DynamoDB table to scan"
                            },
                            "filter_expression": {
                                "type": "string",
                                "description": "Optional filter expression (e.g., 'attribute_exists(email)')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of items to return (default: 25)",
                                "default": 25
                            },
                            "projection_expression": {
                                "type": "string",
                                "description": "Comma-separated list of attributes to return"
                            }
                        },
                        "required": ["table_name"]
                    },
                    annotations={}
                ),
                Tool(
                    name="query_table",
                    description="Query a DynamoDB table using partition key and optional sort key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the DynamoDB table to query"
                            },
                            "key_condition_expression": {
                                "type": "string",
                                "description": "Key condition expression (e.g., 'pk = :pk_val')"
                            },
                            "expression_attribute_values": {
                                "type": "object",
                                "description": "Attribute values for the expression (e.g., {':pk_val': 'user123'})"
                            },
                            "filter_expression": {
                                "type": "string",
                                "description": "Optional filter expression"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of items to return (default: 25)",
                                "default": 25
                            },
                            "projection_expression": {
                                "type": "string",
                                "description": "Comma-separated list of attributes to return"
                            }
                        },
                        "required": ["table_name", "key_condition_expression", "expression_attribute_values"]
                    },
                    annotations={}
                ),
                Tool(
                    name="get_item",
                    description="Get a specific item from DynamoDB table by primary key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the DynamoDB table"
                            },
                            "key": {
                                "type": "object",
                                "description": "Primary key of the item (e.g., {'id': 'user123'})"
                            },
                            "projection_expression": {
                                "type": "string",
                                "description": "Comma-separated list of attributes to return"
                            }
                        },
                        "required": ["table_name", "key"]
                    },
                    annotations={}
                ),
                Tool(
                    name="analyze_table_structure",
                    description="Analyze table structure and provide insights about data patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the DynamoDB table to analyze"
                            },
                            "sample_size": {
                                "type": "integer",
                                "description": "Number of items to sample for analysis (default: 100)",
                                "default": 100
                            }
                        },
                        "required": ["table_name"]
                    },
                    annotations={}
                )
            ]
            return ListToolsResult(tools=tools)
        
        # Store the handler function for direct access
        self.handlers['list_tools'] = list_tools
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "scan_table":
                    return await self._scan_table(request.arguments)
                elif request.name == "query_table":
                    return await self._query_table(request.arguments)
                elif request.name == "get_item":
                    return await self._get_item(request.arguments)
                elif request.name == "analyze_table_structure":
                    return await self._analyze_table_structure(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
                    
            except Exception as e:
                logger.error(f"Error calling tool {request.name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    ]
                )
        
        # Store the handler function for direct access
        self.handlers['call_tool'] = call_tool
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available analysis prompts"""
            prompts = [
                Prompt(
                    name="data_summary",
                    description="Generate a comprehensive summary of table data including key metrics and patterns",
                    arguments=[
                        {
                            "name": "table_name",
                            "description": "Name of the DynamoDB table to analyze",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="find_anomalies",
                    description="Identify potential data anomalies and inconsistencies in the table",
                    arguments=[
                        {
                            "name": "table_name",
                            "description": "Name of the DynamoDB table to analyze",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="usage_patterns",
                    description="Analyze usage patterns and access patterns for optimization recommendations",
                    arguments=[
                        {
                            "name": "table_name",
                            "description": "Name of the DynamoDB table to analyze",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="data_quality_report",
                    description="Generate a comprehensive data quality report with recommendations",
                    arguments=[
                        {
                            "name": "table_name",
                            "description": "Name of the DynamoDB table to analyze",
                            "required": True
                        }
                    ]
                )
            ]
            return ListPromptsResult(prompts=prompts)
        
        # Store the handler function for direct access
        self.handlers['list_prompts'] = list_prompts
        
        @self.server.get_prompt()
        async def get_prompt(request: GetPromptRequest) -> GetPromptResult:
            """Get specific analysis prompt"""
            table_name = request.arguments.get("table_name", "")
            
            if request.name == "data_summary":
                message = f"""Please analyze the DynamoDB table '{table_name}' and provide a comprehensive summary including:

                            1. **Table Overview**
                            - Total number of items
                            - Key schema and attribute definitions
                            - Table size and storage utilization

                            2. **Data Distribution**
                            - Most common attribute patterns
                            - Value distribution for key attributes
                            - Null/missing value analysis

                            3. **Key Insights**
                            - Data trends and patterns
                            - Potential optimization opportunities
                            - Any notable characteristics

                            Use the available MCP tools to gather this information and present it in a clear, actionable format."""

            elif request.name == "find_anomalies":
                message = f"""Analyze the DynamoDB table '{table_name}' to identify potential anomalies and data quality issues:

                            1. **Data Consistency Issues**
                            - Inconsistent data formats
                            - Unexpected null values
                            - Duplicate or near-duplicate records

                            2. **Value Anomalies**
                            - Outliers in numerical fields
                            - Unusual string patterns
                            - Date/timestamp inconsistencies

                            3. **Structural Issues**
                            - Missing expected attributes
                            - Unexpected attribute types
                            - Schema evolution problems

                            Use sampling techniques to efficiently identify issues without scanning the entire table."""

            elif request.name == "usage_patterns":
                message = f"""Analyze the DynamoDB table '{table_name}' for usage patterns and optimization opportunities:

                        1. **Access Patterns**
                        - Most frequently accessed items
                        - Query vs scan usage implications
                        - Hot partition analysis

                        2. **Performance Optimization**
                        - Index utilization recommendations
                        - Partition key distribution
                        - Query efficiency suggestions

                        3. **Cost Optimization**
                        - Storage optimization opportunities
                        - Read/write capacity recommendations
                        - TTL implementation suggestions

                        Focus on actionable recommendations for improving performance and reducing costs."""

            elif request.name == "data_quality_report":
                message = f"""Generate a comprehensive data quality report for DynamoDB table '{table_name}':

                        1. **Completeness Assessment**
                        - Required field coverage
                        - Missing data patterns
                        - Data population rates

                        2. **Accuracy Validation**
                        - Data format consistency
                        - Value range validation
                        - Cross-field consistency checks

                        3. **Data Quality Score**
                        - Overall quality metrics
                        - Improvement recommendations
                        - Priority areas for cleanup

                        4. **Action Plan**
                        - Immediate fixes needed
                        - Long-term data governance suggestions
                        - Monitoring recommendations

                        Provide specific, actionable recommendations with priority levels."""

            else:
                message = f"Unknown prompt: {request.name}"

            return GetPromptResult(
                description=f"Analysis prompt for DynamoDB table operations",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=message)
                    )
                ]
            )
        
        # Store the handler function for direct access
        self.handlers['get_prompt'] = get_prompt
    
    async def _scan_table(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Scan DynamoDB table"""
        table_name = arguments["table_name"]
        
        if table_name not in self.table_names:
            raise ValueError(f"Table {table_name} not found")
        
        table = self.dynamodb.Table(table_name)
        
        # Build scan parameters
        scan_params = {
            "Limit": arguments.get("limit", 25)
        }
        
        if "filter_expression" in arguments:
            scan_params["FilterExpression"] = arguments["filter_expression"]
        
        if "projection_expression" in arguments:
            scan_params["ProjectionExpression"] = arguments["projection_expression"]
        
        response = table.scan(**scan_params)
        
        result = {
            "items": response.get("Items", []),
            "count": response.get("Count", 0),
            "scanned_count": response.get("ScannedCount", 0),
            "last_evaluated_key": response.get("LastEvaluatedKey")
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, cls=DecimalEncoder, indent=2)
                )
            ]
        )
    
    async def _query_table(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Query DynamoDB table"""
        table_name = arguments["table_name"]
        
        if table_name not in self.table_names:
            raise ValueError(f"Table {table_name} not found")
        
        table = self.dynamodb.Table(table_name)
        
        # Build query parameters
        query_params = {
            "KeyConditionExpression": arguments["key_condition_expression"],
            "ExpressionAttributeValues": arguments["expression_attribute_values"],
            "Limit": arguments.get("limit", 25)
        }
        
        if "filter_expression" in arguments:
            query_params["FilterExpression"] = arguments["filter_expression"]
        
        if "projection_expression" in arguments:
            query_params["ProjectionExpression"] = arguments["projection_expression"]
        
        response = table.query(**query_params)
        
        result = {
            "items": response.get("Items", []),
            "count": response.get("Count", 0),
            "scanned_count": response.get("ScannedCount", 0),
            "last_evaluated_key": response.get("LastEvaluatedKey")
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, cls=DecimalEncoder, indent=2)
                )
            ]
        )
    
    async def _get_item(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get specific item from DynamoDB table"""
        table_name = arguments["table_name"]
        
        if table_name not in self.table_names:
            raise ValueError(f"Table {table_name} not found")
        
        table = self.dynamodb.Table(table_name)
        
        # Build get_item parameters
        get_params = {
            "Key": arguments["key"]
        }
        
        if "projection_expression" in arguments:
            get_params["ProjectionExpression"] = arguments["projection_expression"]
        
        response = table.get_item(**get_params)
        
        result = {
            "item": response.get("Item"),
            "found": "Item" in response
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, cls=DecimalEncoder, indent=2)
                )
            ]
        )
    
    async def _analyze_table_structure(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Analyze table structure and data patterns"""
        table_name = arguments["table_name"]
        sample_size = arguments.get("sample_size", 100)
        
        if table_name not in self.table_names:
            raise ValueError(f"Table {table_name} not found")
        
        table = self.dynamodb.Table(table_name)
        
        # Get table metadata
        analysis = {
            "table_name": table_name,
            "table_status": table.table_status,
            "item_count": table.item_count,
            "table_size_bytes": table.table_size_bytes,
            "key_schema": table.key_schema,
            "attribute_definitions": table.attribute_definitions,
        }
        
        # Sample data for pattern analysis
        try:
            response = table.scan(Limit=sample_size)
            items = response.get("Items", [])
            
            if items:
                # Analyze attribute patterns
                all_attributes = set()
                attribute_types = {}
                null_counts = {}
                
                for item in items:
                    for key, value in item.items():
                        all_attributes.add(key)
                        
                        # Track attribute types
                        value_type = type(value).__name__
                        if key not in attribute_types:
                            attribute_types[key] = {}
                        attribute_types[key][value_type] = attribute_types[key].get(value_type, 0) + 1
                        
                        # Track null/empty values
                        if value is None or value == "":
                            null_counts[key] = null_counts.get(key, 0) + 1
                
                analysis["sample_analysis"] = {
                    "sample_size": len(items),
                    "unique_attributes": list(all_attributes),
                    "attribute_count": len(all_attributes),
                    "attribute_types": attribute_types,
                    "null_empty_counts": null_counts,
                    "data_completeness": {
                        attr: (len(items) - null_counts.get(attr, 0)) / len(items) * 100
                        for attr in all_attributes
                    }
                }
                
        except Exception as e:
            analysis["sample_analysis_error"] = str(e)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(analysis, cls=DecimalEncoder, indent=2)
                )
            ]
        )

# FastAPI wrapper for API Gateway integration
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="DynamoDB MCP Server", version="1.0.0")

# Global MCP server instance
mcp_server_instance = None

@app.on_event("startup")
async def startup_event():
    global mcp_server_instance
    mcp_server_instance = DynamoDBMCPServer()
    logger.info("MCP Server initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint for ECS"""
    return {"status": "healthy", "tables": mcp_server_instance.table_names if mcp_server_instance else []}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP protocol endpoint"""
    if not mcp_server_instance:
        raise HTTPException(status_code=503, detail="MCP Server not initialized")
    
    try:
        # Get the JSON payload
        payload = await request.json()
        
        # Route to appropriate MCP handler based on method
        method = payload.get("method", "")
        
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {"resources": {"subscribe": False, "listChanged": False}, "tools": {"listChanged": False}, "prompts": {"listChanged": False}}, "serverInfo": {"name": "dynamodb-mcp-server", "version": "1.0.0"}}}
        elif method == "resources/list":
            result = await mcp_server_instance.handlers['list_resources']()
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result.model_dump(exclude_none=True)}
        elif method == "resources/read":
            params = payload.get("params", {})
            result = await mcp_server_instance.handlers['read_resource'](ReadResourceRequest(uri=params.get("uri", "")))
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result.model_dump(exclude_none=True)}
        elif method == "tools/list":
            result = await mcp_server_instance.handlers['list_tools']()
            # Convert to dict and remove null values
            result_dict = result.model_dump(exclude_none=True)
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result_dict}
        elif method == "tools/call":
            params = payload.get("params", {})
            result = await mcp_server_instance.handlers['call_tool'](CallToolRequest(name=params.get("name", ""), arguments=params.get("arguments", {})))
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result.model_dump(exclude_none=True)}
        elif method == "prompts/list":
            result = await mcp_server_instance.handlers['list_prompts']()
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result.model_dump(exclude_none=True)}
        elif method == "prompts/get":
            params = payload.get("params", {})
            result = await mcp_server_instance.handlers['get_prompt'](GetPromptRequest(name=params.get("name", ""), arguments=params.get("arguments", {})))
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": result.model_dump(exclude_none=True)}
        else:
            return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32601, "message": f"Method not found: {method}"}}
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {"jsonrpc": "2.0", "id": payload.get("id", None), "error": {"code": -32603, "message": str(e)}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))