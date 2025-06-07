## DynamoDB MCP Server POC

This mcp server is for dynamDB.

### How to run
1. Create and activate a virtual environment:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```
3. Set AWS ENv
    ```bash
    export AWS_DEFAULT_REGION="eu-central-1"
    export AWS_REGION="eu-central-1"
    export AWS_ACCESS_KEY_ID="xxx"
    export AWS_SECRET_ACCESS_KEY="xxx"
    ```

4. Run the MCP server:

    ```bash
    python mcp_server.py
    ```

5. Validating it using mcp inspector
    ```bash
    npx @modelcontextprotocol/inspector
    ```