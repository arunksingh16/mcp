import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { GetPromptResult } from '@modelcontextprotocol/sdk/types';
import { z } from 'zod';

export const initializeServer = (): McpServer => {
    // Create an MCP server with implementation details
    const server = new McpServer({
      name: 'prompt-gallery-server',
      version: '1.0.0',
    }, { capabilities: { logging: {} } });

     // Register a simple prompt
    server.prompt(
        'greeting-template',
        'A simple greeting prompt template',
        {
        name: z.string().describe('Name to include in greeting'),
        },
        async ({ name }): Promise<GetPromptResult> => {
        return {
            messages: [
            {
                role: 'user',
                content: {
                type: 'text',
                text: `Please greet ${name} in a friendly manner.`,
                },
            },
            ],
        };
        }
    );

    // Register a calculator tool
    server.tool(
        'calculator',
        'A simple calculator tool that performs basic arithmetic operations',
        {
            a: z.number().describe('First number'),
            b: z.number().describe('Second number'),
            operation: z.enum(['add', 'subtract', 'multiply', 'divide']).describe('Math operation to perform')
        },
        async ({ a, b, operation }) => {
            let result: number;
            switch (operation) {
                case 'add':
                    result = a + b;
                    break;
                case 'subtract':
                    result = a - b;
                    break;
                case 'multiply':
                    result = a * b;
                    break;
                case 'divide':
                    if (b === 0) {
                        return {
                            content: [{
                                type: "text",
                                text: "Error: Cannot divide by zero"
                            }]
                        };
                    }
                    result = a / b;
                    break;
                default:
                    return {
                        content: [{
                            type: "text",
                            text: "Error: Invalid operation"
                        }]
                    };
            }
            
            return {
                content: [{
                    type: "text",
                    text: String(result)
                }]
            };
        }
    );

    return server
}