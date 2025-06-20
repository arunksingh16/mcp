import express, { Request, Response } from "express";
import { initializeServer } from "./lambda"; // Adjust the import path as needed
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const app = express()
const port = process.env['PORT'] || 3000

// SIGTERM Handler
process.on('SIGTERM', async () => {
    console.info('[express] SIGTERM received');

    console.info('[express] cleaning up');
    // perform actual clean up work here.
    await new Promise(resolve => setTimeout(resolve, 100));

    console.info('[express] exiting');
    process.exit(0)
});

app.use(express.json());

app.post("/mcp", async (req, res) => {
  const server = initializeServer();
  try {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    await server.connect(transport);

    await transport.handleRequest(req, res, req.body);

    req.on("close", () => {
      console.log("Request closed");
      transport.close();
      server.close();
    });
  } catch (e) {
    console.error("Error handling MCP request:", e);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal server error",
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
    console.log('Received GET MCP request');
    res.writeHead(405).end(JSON.stringify({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    }));
  });

  app.delete('/mcp', async (req: Request, res: Response) => {
    console.log('Received DELETE MCP request');
    res.writeHead(405).end(JSON.stringify({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    }));
  });

const PORT = process.env.PORT || 3000;

if (process.env.AWS_LAMBDA_FUNCTION_NAME) {
  // Running in Lambda - export the app for Lambda Web Adapter
  module.exports = app;
  exports.handler = app;
} else {
  // Running locally
  app.listen(PORT, () => {
    console.log(`MCP server running on ${PORT}`)
  });
}


app.listen(port, () => {
    console.log(`MCP app listening at http://localhost:${port}`)
})