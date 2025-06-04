#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { InfraStack } from '../lib/infra-stack';
import { VpcStack } from '../lib/vpc';
const app = new cdk.App();

// Define common props with explicit region to ensure consistency
const envProps = { 
  env: { 
    region: 'eu-west-1' // Set this to match your ECR region
  }
};

const VPC = new VpcStack(app, 'VpcStack', envProps);

new InfraStack(app, 'InfraStack', {
  vpc: VPC.vpc,
  ...envProps
});