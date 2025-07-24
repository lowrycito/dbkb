# Database Knowledge Base (DBKB) - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying changes to the Database Knowledge Base (DBKB) service running on AWS ECS Fargate with Amazon Bedrock and Claude Sonnet 4.

## Architecture

- **Application**: FastAPI-based REST API with Claude Sonnet 4 integration
- **Container**: Docker image running on ARM64 architecture
- **Orchestration**: AWS ECS Fargate cluster (`dbkb-cluster`)
- **Load Balancer**: Application Load Balancer with HTTPS termination
- **AI/ML**: Amazon Bedrock with Claude Sonnet 4 cross-region inference
- **Knowledge Base**: Amazon Bedrock Knowledge Base (ID: `KRD3MW7QFS`)

## Prerequisites

### Required Tools
```bash
# AWS CLI v2
aws --version

# Docker with buildx support
docker --version
docker buildx version

# jq for JSON processing
jq --version
```

### AWS Credentials
Ensure your AWS credentials have the following permissions:
- ECR: `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`
- ECS: `ecs:UpdateService`, `ecs:DescribeServices`, `ecs:DescribeTasks`
- IAM: `iam:CreatePolicyVersion`, `iam:DeletePolicyVersion` (if updating policies)
- Logs: `logs:DescribeLogStreams`, `logs:GetLogEvents`

### Environment Variables
```bash
export AWS_DEFAULT_REGION=us-east-1
export ECR_REGISTRY=836255806547.dkr.ecr.us-east-1.amazonaws.com
export ECR_REPOSITORY=dbkb-api
export ECS_CLUSTER=dbkb-cluster
export ECS_SERVICE=dbkb-service
```

## Deployment Process

### Step 1: Prepare for Deployment

1. **Navigate to project directory**:
   ```bash
   cd /path/to/dbkb
   ```

2. **Verify current service status**:
   ```bash
   aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].{status: status, runningCount: runningCount, desiredCount: desiredCount}'
   ```

3. **Check current health**:
   ```bash
   curl -k -s "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"
   ```

### Step 2: Build and Push Docker Image

1. **Login to ECR**:
   ```bash
   aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
   ```

2. **Build ARM64 image** (required for Fargate):
   ```bash
   docker buildx build --platform linux/arm64 -t $ECR_REPOSITORY:latest .
   ```

3. **Tag for ECR**:
   ```bash
   docker tag $ECR_REPOSITORY:latest $ECR_REGISTRY/$ECR_REPOSITORY:latest
   ```

4. **Push to ECR**:
   ```bash
   docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
   ```

### Step 3: Deploy to ECS

1. **Force new deployment**:
   ```bash
   aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --query 'service.serviceName'
   ```

2. **Monitor deployment status**:
   ```bash
   # Check deployment progress
   aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].deployments[0].rolloutState'
   
   # Watch for completion (repeat until "COMPLETED")
   watch -n 10 'aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query "services[0].deployments[0].rolloutState"'
   ```

3. **Verify health after deployment**:
   ```bash
   # Wait for load balancer health checks
   sleep 60
   
   # Test health endpoint
   curl -k -s "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"
   ```

### Step 4: Validate Deployment

1. **Test API functionality**:
   ```bash
   # Test basic query
   curl -k -s "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
     -H "Content-Type: application/json" \
     -d '{"query_text": "what tables are in this database?", "extended_thinking": false, "include_contexts": false, "include_thinking": false}' \
     | jq -r '.answer' | head -10
   ```

2. **Check application logs**:
   ```bash
   # Get current task ID
   TASK_ID=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name $ECS_SERVICE --query 'taskArns[0]' | tr -d '"' | xargs basename)
   
   # View recent logs
   aws logs get-log-events --log-group-name "/aws/ecs/dbkb-api" --log-stream-name "ecs/dbkb-container/$TASK_ID" --query 'events[-10:]'
   ```

## Quick Deployment Script

Save this as `deploy.sh` for quick deployments:

```bash
#!/bin/bash
set -e

# Configuration
export AWS_DEFAULT_REGION=us-east-1
export ECR_REGISTRY=836255806547.dkr.ecr.us-east-1.amazonaws.com
export ECR_REPOSITORY=dbkb-api
export ECS_CLUSTER=dbkb-cluster
export ECS_SERVICE=dbkb-service

echo "🚀 Starting DBKB deployment..."

# Login to ECR
echo "📦 Logging in to ECR..."
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push image
echo "🔨 Building ARM64 Docker image..."
docker buildx build --platform linux/arm64 -t $ECR_REPOSITORY:latest .

echo "🏷️ Tagging image for ECR..."
docker tag $ECR_REPOSITORY:latest $ECR_REGISTRY/$ECR_REPOSITORY:latest

echo "📤 Pushing to ECR..."
docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

# Deploy to ECS
echo "🚢 Deploying to ECS..."
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --query 'service.serviceName'

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
while true; do
    STATUS=$(aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].deployments[0].rolloutState' --output text)
    echo "Deployment status: $STATUS"
    if [ "$STATUS" = "COMPLETED" ]; then
        break
    fi
    sleep 15
done

# Health check
echo "🏥 Checking service health..."
sleep 30
HEALTH=$(curl -k -s "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health" | jq -r '.status')
echo "Health status: $HEALTH"

# Test API
echo "🧪 Testing API functionality..."
curl -k -s "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test deployment", "extended_thinking": false, "include_contexts": false, "include_thinking": false}' \
  | jq -r '.answer' | head -3

echo "✅ Deployment completed successfully!"
```

## Configuration Management

### Environment Variables (ECS Task Definition)
- `AWS_DEFAULT_REGION`: us-east-1
- `LOG_LEVEL`: INFO
- `KNOWLEDGE_BASE_ID`: KRD3MW7QFS

### IAM Roles and Policies

**Task Role**: `dbkb-ecs-task-role`
- Policy: `dbkb-bedrock-policy-5c5c903` (current version: v6)
- Permissions: Bedrock model invocation, Knowledge Base access, S3, CloudWatch Logs

**Execution Role**: `dbkb-task-execution-role-004327c`
- Permissions: ECR image pull, CloudWatch Logs creation

### Current Model Configuration
- **Model**: Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`)
- **Type**: Cross-region inference profile
- **Fallback**: Graceful error handling with context-based responses

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Check IAM policy version
aws iam get-policy-version --policy-arn arn:aws:iam::836255806547:policy/dbkb-bedrock-policy-5c5c903 --version-id v6
```

#### 2. Deployment Stuck
```bash
# Check service events
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].events[0:5]'

# Force stop current tasks if needed
aws ecs list-tasks --cluster $ECS_CLUSTER --service-name $ECS_SERVICE --query 'taskArns[0]' | xargs -I {} aws ecs stop-task --cluster $ECS_CLUSTER --task {}
```

#### 3. Health Check Failures
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:836255806547:targetgroup/dbkb-tg/776726325fad6928
```

#### 4. Model Access Issues
```bash
# Check for permission errors in logs
aws logs filter-log-events --log-group-name "/aws/ecs/dbkb-api" --filter-pattern "AccessDeniedException"
```

### Log Analysis
```bash
# Search for errors
aws logs filter-log-events --log-group-name "/aws/ecs/dbkb-api" --filter-pattern "ERROR" --start-time $(date -d '1 hour ago' +%s)000

# Monitor real-time logs (if available)
aws logs tail /aws/ecs/dbkb-api --follow
```

## Rollback Procedures

### Emergency Rollback
If deployment fails and service is unhealthy:

1. **Stop failed deployment**:
   ```bash
   aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --desired-count 0
   aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --desired-count 1
   ```

2. **Use previous image** (if available):
   ```bash
   # List recent images
   aws ecr describe-images --repository-name $ECR_REPOSITORY --query 'imageDetails[*].{digest: imageDigest, pushed: imagePushedAt}' --output table
   
   # Update task definition with specific image digest if needed
   ```

### Code Rollback
```bash
# Reset to last known good commit
git log --oneline -10
git checkout <good-commit-hash>

# Rebuild and deploy
docker buildx build --platform linux/arm64 -t $ECR_REPOSITORY:rollback .
# ... continue with deployment steps
```

## Performance Monitoring

### Key Metrics to Monitor
- ECS Service CPU/Memory utilization
- Load Balancer response times
- Bedrock API call latency
- Error rates in CloudWatch Logs

### Monitoring Commands
```bash
# Service resource utilization
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --query 'services[0].{runningCount: runningCount, pendingCount: pendingCount}'

# Load balancer metrics
aws logs filter-log-events --log-group-name "/aws/elasticloadbalancing/app/dbkb-alb/db94df04cdbed257" --start-time $(date -d '1 hour ago' +%s)000
```

## Security Considerations

### SSL/TLS
- Load balancer handles SSL termination
- Internal communication between ALB and ECS is HTTP
- Application supports HTTPS health checks

### Network Security
- ECS tasks run in private subnets with public IP assignment
- Security group: `sg-07dfcf606159c004c`
- Only port 8000 exposed internally

### Secrets Management
- No hardcoded secrets in container
- AWS credentials provided via IAM roles
- Knowledge Base ID passed as environment variable

## Contact and Support

For deployment issues:
1. Check CloudWatch Logs: `/aws/ecs/dbkb-api`
2. Review ECS service events
3. Validate IAM permissions
4. Test Bedrock model access

Current endpoint: `https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/`
