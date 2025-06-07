## MCP Server for Copilot APIs

```
docker build -t mcp-server:stdio .
docker run -it --rm -e API_KEY="xxx" -e MCP_SERVER_MODE="stdio" mcp-server:stdio

```

Locally

```
export MCP_SERVER_MODE="stdio"
export API_KEY="xxx"
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```