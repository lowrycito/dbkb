# Complete DBKB Deployment Guide
## Database Knowledge Base - Industry-Based Architecture

This guide provides step-by-step instructions for deploying the DBKB system with the new industry-based knowledge base architecture.

## 📋 Prerequisites

### Required Tools
- **AWS CLI v2** with configured credentials
- **Docker** with buildx support for ARM64 builds
- **Pulumi CLI** installed and logged in
- **MySQL client** for database setup
- **jq** for JSON processing (optional but helpful)

### AWS Permissions Required
Your AWS credentials must have permissions for:
- ECR: Container registry operations
- ECS: Service and task management  
- IAM: Role and policy management
- EC2: VPC, security group, and load balancer operations
- SSM: Parameter Store access
- CloudWatch: Logs access

### Environment Setup
```bash
# Set required environment variables
export AWS_DEFAULT_REGION=us-east-1
export ECR_REGISTRY=836255806547.dkr.ecr.us-east-1.amazonaws.com
export ECR_REPOSITORY=dbkb-api
export ECS_CLUSTER=dbkb-cluster
export ECS_SERVICE=dbkb-service
```

## 🗄️ Step 1: Database Setup

### 1.1 Create New Schema
Connect to your Aurora MySQL database and create the new schema:

```bash
# Connect to Aurora database
mysql -h dev.writer.pic.picbusiness.aws -u your_username -p

# Create the chat database
CREATE DATABASE IF NOT EXISTS chat;
USE chat;
```

### 1.2 Deploy New Schema
Run the updated schema file:

```bash
# From the project root directory
mysql -h dev.writer.pic.picbusiness.aws -u your_username -p chat < database_schema_chat.sql
```

### 1.3 Verify Schema Installation
```sql
-- Check that all tables were created
SHOW TABLES;
-- Should show: application, company, user, chat_session, chat_message, query_analytic, user_preference

-- Verify sample applications
SELECT Name, DisplayName, DatabaseKnowledgeBaseId, SupportKnowledgeBaseId, DocumentationKnowledgeBaseId 
FROM application;

-- Verify sample companies
SELECT c.CompanyCode, c.CompanyName, a.Name as Application 
FROM company c 
JOIN application a ON c.ApplicationId = a.Id;
```

### 1.4 Configure Knowledge Base IDs
Update the application table with your actual Knowledge Base IDs:

```sql
-- Update Epic application KBs
UPDATE application SET 
    DatabaseKnowledgeBaseId = 'your-actual-epic-db-kb-id',
    SupportKnowledgeBaseId = 'your-actual-epic-support-kb-id',
    DocumentationKnowledgeBaseId = 'your-actual-epic-docs-kb-id'
WHERE Name = 'epic';

-- Update DIS application KBs  
UPDATE application SET 
    DatabaseKnowledgeBaseId = 'your-actual-dis-db-kb-id',
    SupportKnowledgeBaseId = 'your-actual-dis-support-kb-id',
    DocumentationKnowledgeBaseId = 'your-actual-dis-docs-kb-id'
WHERE Name = 'dis';

-- Update PPD application KBs
UPDATE application SET 
    DatabaseKnowledgeBaseId = 'your-actual-ppd-db-kb-id',
    SupportKnowledgeBaseId = 'your-actual-ppd-support-kb-id',
    DocumentationKnowledgeBaseId = 'your-actual-ppd-docs-kb-id'
WHERE Name = 'ppd';
```

## 🔐 Step 2: AWS Systems Manager (SSM) Parameter Setup

### 2.1 Create Database Credentials
Set up secure database credentials in SSM Parameter Store:

```bash
# Create username parameter
aws ssm put-parameter \
  --name "/dbkb/chat/db/username" \
  --value "your_actual_database_username" \
  --type "String" \
  --description "Username for DBKB chat database" \
  --region us-east-1

# Create password parameter (SecureString for encryption)
aws ssm put-parameter \
  --name "/dbkb/chat/db/password" \
  --value "your_actual_database_password" \
  --type "SecureString" \
  --description "Password for DBKB chat database" \
  --region us-east-1
```

### 2.2 Verify SSM Parameters
```bash
# Check username parameter
aws ssm get-parameter --name "/dbkb/chat/db/username" --region us-east-1

# Check password parameter (with decryption)
aws ssm get-parameter --name "/dbkb/chat/db/password" --with-decryption --region us-east-1
```

## 🐳 Step 3: Container Build and Push

### 3.1 Build ARM64 Container
ECS Fargate requires ARM64 architecture:

```bash
# Navigate to project root
cd /path/to/dbkb

# Login to ECR
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build ARM64 container (required for Fargate)
docker buildx build --platform linux/arm64 -t $ECR_REPOSITORY:latest .

# Tag for ECR
docker tag $ECR_REPOSITORY:latest $ECR_REGISTRY/$ECR_REPOSITORY:latest

# Push to ECR
docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

### 3.2 Verify Container Push
```bash
# List images in ECR repository
aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_DEFAULT_REGION
```

## 🏗️ Step 4: Infrastructure Deployment

### 4.1 Deploy with Pulumi
```bash
# Navigate to infrastructure directory
cd infrastructure

# Ensure Pulumi is logged in
pulumi login

# Initialize or select stack
pulumi stack init dev  # or pulumi stack select dev

# Deploy infrastructure
pulumi up
```

### 4.2 VPC Configuration Fix (If Needed)
If you encounter VPC-related errors during deployment, run the fix script:

```bash
# Fix VPC deployment issue (if resources were deployed to wrong VPC)
./fix_vpc_deployment.sh
```

This script will:
- Remove ECS resources from the wrong VPC
- Redeploy them to the correct VPC (vpc-f93ec29f) 
- Automatically configure security group rules
- Test the deployment

### 4.3 Verify Deployment
```bash
# Check ECS service status
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region us-east-1

# Check load balancer health
ALB_DNS=$(pulumi stack output alb_dns_name)
curl -k "https://$ALB_DNS/health"
```

## 🧪 Step 5: Testing and Validation

### 5.1 Test API Health
```bash
# Basic health check
curl -k "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"

# Expected response:
# {"status": "healthy", "timestamp": "...", "version": "..."}
```

### 5.2 Test Multi-KB Query Endpoint
```bash
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What tables are in the database?",
    "userContext": {
      "loginId": "test123",
      "email": "test@company.com",
      "firstName": "Test",
      "lastName": "User", 
      "company": "TEST001",
      "companyName": "Test Company",
      "industry": "Healthcare",
      "databaseHost": "test-db.example.com",
      "databaseSchema": "test_schema",
      "application": "epic"
    },
    "queryMode": "smart"
  }'
```

### 5.3 Test UI Access
Create test URLs for each application:

**Epic Application Test:**
```
https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/?Application=epic&DatabaseHost=epic-db.example.com&DatabaseSchema=epic_prod&Company=HOSPITAL001&CompanyName=General%20Hospital&Industry=Healthcare&LoginId=dr.smith&FirstName=John&LastName=Smith&Email=dr.smith@hospital.com
```

**DIS Application Test:**
```
https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/?Application=dis&DatabaseHost=dis-db.example.com&DatabaseSchema=dis_prod&Company=WAREHOUSE001&CompanyName=Distribution%20Co&Industry=Logistics&LoginId=manager.davis&FirstName=Bob&LastName=Davis&Email=bob@distributionco.com
```

**PPD Application Test:**
```
https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/?Application=ppd&DatabaseHost=ppd-db.example.com&DatabaseSchema=ppd_main&Company=CONSTRUCTION001&CompanyName=BuildCorp%20Inc&Industry=Construction&LoginId=pm.wilson&FirstName=Alice&LastName=Wilson&Email=alice@buildcorp.com
```

### 5.4 Test Query Classification
Test that queries route to correct knowledge bases:

```bash
# Test database-specific query
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me the table relationships and foreign keys",
    "userContext": {...},
    "queryMode": "smart"
  }' | jq '.source_type'

# Test support-specific query  
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "I am getting an error when trying to save data",
    "userContext": {...},
    "queryMode": "smart"  
  }' | jq '.source_type'

# Test documentation-specific query
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "How do I configure the system for first time use?",
    "userContext": {...},
    "queryMode": "smart"
  }' | jq '.source_type'
```

## 📊 Step 6: Monitoring and Logs

### 6.1 Check Application Logs
```bash
# Get current task ARN
TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name $ECS_SERVICE --query 'taskArns[0]' --output text)

# View recent logs
aws logs get-log-events \
  --log-group-name "/aws/ecs/dbkb-api" \
  --log-stream-name "ecs/dbkb-container/$(basename $TASK_ARN)" \
  --start-time $(($(date +%s) - 3600))000

# Monitor real-time logs (if available)
aws logs tail /aws/ecs/dbkb-api --follow
```

### 6.2 Monitor ECS Service
```bash
# Check service status
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE \
  --query 'services[0].{status: status, runningCount: runningCount, desiredCount: desiredCount}'

# Check task health
aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN \
  --query 'tasks[0].{lastStatus: lastStatus, healthStatus: healthStatus}'
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Security Group Access Issues
**Symptom:** Database connection errors in logs
**Solution:**
```bash
# Verify ECS security group can reach database
ECS_SG_ID=$(pulumi stack output ecs_security_group_id)
aws ec2 describe-security-groups --group-ids sg-94cf59e9 --query 'SecurityGroups[0].IpPermissions'

# If rule is missing, add it:
aws ec2 authorize-security-group-ingress \
  --group-id sg-94cf59e9 \
  --protocol tcp \
  --port 3306 \
  --source-group $ECS_SG_ID
```

#### 2. SSM Parameter Access Issues  
**Symptom:** "Failed to retrieve SSM parameters" in logs
**Solution:**
```bash
# Check IAM role permissions
TASK_ROLE_ARN=$(pulumi stack output task_role_arn)
aws iam simulate-principal-policy \
  --policy-source-arn $TASK_ROLE_ARN \
  --action-names ssm:GetParameter \
  --resource-arns "arn:aws:ssm:us-east-1:*:parameter/dbkb/chat/db/*"
```

#### 3. Knowledge Base Access Issues
**Symptom:** "AccessDeniedException" when querying KBs
**Solution:**
```bash
# Check Bedrock permissions in task role
aws iam get-role-policy --role-name $(basename $TASK_ROLE_ARN) --policy-name dbkb-bedrock-policy
```

#### 4. Container Build Issues
**Symptom:** Container fails to start
**Solution:**
```bash
# Test container locally first
docker run --platform linux/arm64 -p 8000:8000 -e LOG_LEVEL=DEBUG $ECR_REPOSITORY:latest

# Check container logs
docker logs $(docker ps -lq)
```

## 📝 Post-Deployment Configuration

### 1. Update Knowledge Base IDs
After deployment, update your actual Knowledge Base IDs in the database:

```sql
-- Replace with your actual KB IDs
UPDATE application SET DatabaseKnowledgeBaseId = 'ACTUAL_KB_ID' WHERE Name = 'epic';
-- Repeat for support and documentation KBs
```

### 2. Configure Company Records
Add your actual companies to the system:

```sql
-- Example company setup
INSERT INTO company (CompanyCode, CompanyName, Industry, DatabaseHost, DatabaseSchema, ApplicationId)
VALUES ('YOUR_COMPANY', 'Your Company Name', 'Your Industry', 'your-db-host', 'your-schema', 
        (SELECT Id FROM application WHERE Name = 'epic'));
```

### 3. Performance Optimization
```bash
# Enable CloudWatch Insights for better log analysis
aws logs create-log-group --log-group-name "/aws/ecs/dbkb-api" --region us-east-1

# Set up CloudWatch alarms for key metrics
aws cloudwatch put-metric-alarm \
  --alarm-name "DBKB-High-CPU" \
  --alarm-description "High CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## 🚀 Quick Deployment Script

Create `deploy.sh` for automated deployment:

```bash
#!/bin/bash
set -e

echo "🚀 Starting DBKB deployment..."

# Build and push container
echo "📦 Building and pushing container..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 836255806547.dkr.ecr.us-east-1.amazonaws.com
docker buildx build --platform linux/arm64 -t dbkb-api:latest .
docker tag dbkb-api:latest 836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api:latest
docker push 836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api:latest

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
cd infrastructure
pulumi up --yes

# Configure security group
echo "🔐 Configuring database access..."
ECS_SG_ID=$(pulumi stack output ecs_security_group_id)
aws ec2 authorize-security-group-ingress \
  --group-id sg-94cf59e9 \
  --protocol tcp \
  --port 3306 \
  --source-group $ECS_SG_ID \
  --region us-east-1 || echo "Security group rule may already exist"

# Wait for deployment
echo "⏳ Waiting for service to be healthy..."
sleep 60

# Test health
ALB_DNS=$(pulumi stack output alb_dns_name)
echo "🧪 Testing deployment..."
curl -k "https://$ALB_DNS/health"

echo "✅ Deployment completed successfully!"
echo "🌐 Application URL: https://$ALB_DNS"
```

## 📋 Deployment Checklist

**Pre-deployment:**
- [ ] AWS CLI configured with proper permissions
- [ ] Docker installed with buildx support
- [ ] Pulumi CLI installed and logged in
- [ ] Database credentials ready
- [ ] Knowledge Base IDs identified

**Database Setup:**
- [ ] Schema deployed successfully
- [ ] Application table populated with KB IDs
- [ ] Sample companies configured
- [ ] SSM parameters created and verified

**Infrastructure Deployment:**
- [ ] Container built for ARM64 and pushed to ECR
- [ ] Pulumi deployment successful
- [ ] Security group rules configured manually
- [ ] ECS service running and healthy

**Testing:**
- [ ] API health check passes
- [ ] Multi-KB endpoint responds correctly
- [ ] UI loads with new parameter format
- [ ] Query classification works correctly
- [ ] Chat history persists

**Production Readiness:**
- [ ] CloudWatch monitoring configured
- [ ] Alarms set up for key metrics
- [ ] Log retention configured
- [ ] Backup strategy in place
- [ ] Security review completed

This completes the comprehensive deployment guide for the DBKB industry-based architecture system.