import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
export class LambdaWebAdapterExampleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const mcpFunction = new lambda.DockerImageFunction(this, 'WebAdapterLambda', {
        code: lambda.DockerImageCode.fromImageAsset(
          path.join(__dirname, '../../app') // 👈 relative path to app dir
        ),
        architecture: lambda.Architecture.X86_64, // Explicitly specify x86_64 architecture
        environment: {
          AWS_LAMBDA_EXEC_WRAPPER: '/opt/extensions/lambda-adapter',
          PORT: '3000',
        },
        timeout: cdk.Duration.seconds(30), // Increased timeout for startup
    });

    const mcpApi = new apigatewayv2.HttpApi(this, 'mcpApi', {
      corsPreflight: {
        allowOrigins: ['*'],
        allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key', 'X-Amz-Security-Token', 'X-Amz-User-Agent'],
        allowMethods: [apigatewayv2.CorsHttpMethod.GET, apigatewayv2.CorsHttpMethod.POST]
      }
    })

    // Create a Lambda integration for the mcpFunction
    const mcpIntegration = new integrations.HttpLambdaIntegration('mcpFunctionIntegration', mcpFunction)
    
    // Add a catch-all route that forwards any request to the mcpFunction
    mcpApi.addRoutes({
      path: '/{proxy+}',
      integration: mcpIntegration
    })

    new cdk.CfnOutput(this, 'mcpApiUrl', {
      value: mcpApi.apiEndpoint
    })

    new cdk.CfnOutput(this, 'FunctionName', {
      value: mcpFunction.functionName,
    });
  }
}
