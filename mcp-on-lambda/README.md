# Lambda Web Adapter Example

This project demonstrates deploying a Node.js Express MCP Server as an AWS Lambda function using the AWS Lambda Web Adapter. The adapter enables running HTTP servers in AWS Lambda without modification, allowing you to deploy traditional web applications as serverless functions.

## Project Structure

```plaintext
lambda-web-adapter-example/
├── app/
│   ├── src/               # Node.js Express application
│   │   ├── index.js       # Express app entry point
│   │   └── package.json   # Node.js dependencies
│   └── Dockerfile         # Container definition for Lambda
└── infra/                 # AWS CDK Infrastructure code
    ├── bin/
    │   └── infra.ts       # CDK app entry point
    ├── lib/
    │   └── infra-stack.ts # CDK stack definition
    └── package.json       # CDK dependencies
```

## Features

- **Express.js Web Application**: Simple web server running on Node.js
- **AWS Lambda Web Adapter**: Enables running HTTP servers in AWS Lambda
- **AWS CDK Infrastructure**: Defines Lambda function and API Gateway
- **Docker Container Deployment**: Packages the application in a container
- **API Gateway Integration**: Exposes the Lambda through HTTP API

## Architecture

This project deploys a Node.js Express application in a Docker container to AWS Lambda. It uses:

1. **AWS Lambda Web Adapter**: A Lambda extension that translates HTTP requests to Lambda events and back
2. **AWS Lambda with Container Image**: Allows running the containerized application in Lambda
3. **Amazon API Gateway HTTP API**: Routes HTTP requests to the Lambda function

## Prerequisites

- [Node.js](https://nodejs.org/) (v16+)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS CDK](https://aws.amazon.com/cdk/) v2 installed (`npm install -g aws-cdk`)
- [Docker](https://www.docker.com/) installed and running

## Setup & Deployment

### 1. Install dependencies

```bash
# Install application dependencies
cd app/src
npm install

# Install CDK dependencies
cd ../../infra
npm install
```

### 2. Bootstrap AWS CDK (first-time only)

```bash
cd infra
cdk bootstrap
```

### 3. Deploy the stack

```bash
cd infra
cdk deploy
```

The deployment will output:

- The API Gateway URL endpoint
- The Lambda function name

## Common Issues and Troubleshooting

### Architecture Mismatch

If you encounter an error like:

```json
{
  "errorType": "Extension.LaunchError",
  "errorMessage": "RequestId: d13ccc80-232d-4a2d-8727-fb9c05c820fb Error: fork/exec /opt/extensions/lambda-adapter: exec format error"
}
```

This indicates an architecture mismatch between your Lambda function and the Lambda Web Adapter binary. To fix:

1. Ensure you're using the correct architecture version in your Dockerfile:

   For x86_64 (Intel/AMD):

   ```dockerfile
   COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1-x86_64 /lambda-adapter /opt/extensions/lambda-adapter
   ```

   For ARM64 (AWS Graviton):

   ```dockerfile
   COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1-arm64 /lambda-adapter /opt/extensions/lambda-adapter
   ```

2. Verify your Lambda function architecture matches:

   ```typescript
   architecture: lambda.Architecture.X86_64, // or lambda.Architecture.ARM_64
   ```

### Permission Issues

Ensure the Lambda Web Adapter has execution permissions:

```dockerfile
RUN chmod +x /opt/extensions/lambda-adapter
```

## Local Development & Testing

### Running Express app locally

```bash
cd app/src
npm install
node index.js
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### Building the container locally

```bash
cd app
docker build -t mcp .
docker run -p 8080:8080 mcp
```

