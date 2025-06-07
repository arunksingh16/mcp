Create a proof-of-concept architecture for deploying simple MCP (Message Control Protocol) servers on AWS using both ECS and Lambda, suitable for an enterprise scenario. The MCP servers must:

1. Use streamable HTTP mechanism for real-time communication (e.g., HTTP chunked transfer or SSE).
2. Be deployable as Docker containers with support for local testing via Docker Compose.
3. Be simple in design and expose only one tool per server.
4. Be placed behind an API Gateway.
5. Store dummy context data in a DynamoDB table.
6. Include a script to populate DynamoDB with mock/dummy data.
7. Enable access to the MCP service via API Gateway endpoint (HTTP).
8. Use huggingface.co dataset or model access for future stages (no need to implement yet).

Generate:
- A Dockerfile for the MCP server.
- A simple FastAPI or Node.js (Express) based MCP server that can stream HTTP responses.
- Docker Compose file to run the MCP server locally and connect to DynamoDB Local.
- AWS CDK definitions to deploy the service on ECS Fargate and as a Lambda behind API Gateway.
- A script (Python or Node.js) to seed DynamoDB with dummy data.
- Folder structure for poc
- GitHub Action for automate this deployment.
- Copilot context file 

Focus on a modular and minimal implementation with working local development and CI/CD-friendly structure.
