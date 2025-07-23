# Multi-Knowledge Base Deployment Guide

## Overview

The DBKB system now supports multiple knowledge bases per customer and can deploy separate API instances for different knowledge base combinations. This guide covers both the new multi-KB UI features and the per-KB deployment infrastructure.

## 🚀 New Multi-KB Features

### 1. **Enhanced URL Parameters**

The UI now accepts multiple knowledge base IDs:

#### Required Parameters:
- `DatabaseKnowledgeBaseId` - Database schema knowledge base
- `DatabaseHost`, `DatabaseSchema`, `Company`, `CompanyName`, `Industry`
- `LoginId`, `FirstName`, `LastName`, `Email`

#### Optional Parameters:
- `SupportKnowledgeBaseId` - Support ticket history knowledge base
- `ProductKnowledgeBaseId` - Product documentation knowledge base

#### Example URL:
```
https://your-domain.com/?
DatabaseKnowledgeBaseId=kb-acme-db-001&
SupportKnowledgeBaseId=kb-acme-support-001&
ProductKnowledgeBaseId=kb-acme-product-001&
Company=ACME001&
CompanyName=Acme%20Corporation&
Industry=Manufacturing&
DatabaseHost=acme-db.cluster-xyz.us-east-1.rds.amazonaws.com&
DatabaseSchema=acme_erp&
LoginId=jsmith&
FirstName=John&
LastName=Smith&
Email=john.smith@acme.com
```

### 2. **Smart Query Routing**

The UI automatically classifies queries and routes them to appropriate knowledge bases:

#### Query Modes:
- **🔍 Smart Search** - Automatically routes based on query content
- **📊 Database Schema** - Query only database knowledge base
- **🎫 Support History** - Query only support knowledge base
- **📚 Product Docs** - Query only product documentation

#### Classification Logic:
- **Database queries**: Contains keywords like "table", "schema", "join", "sql", "column"
- **Support queries**: Contains keywords like "error", "issue", "problem", "slow", "troubleshoot"
- **Product queries**: Contains keywords like "how to", "tutorial", "guide", "setup", "configure"

### 3. **Source Indicators**

Responses show which knowledge base provided the answer:
- 📊 Database - Database schema information
- 🎫 Support - Support ticket history
- 📚 Product - Product documentation

## 🏗️ Per-Knowledge Base API Deployments

### Why Deploy Separate APIs?

1. **Performance**: Dedicated resources per customer/KB combination
2. **Security**: Complete isolation between customers
3. **Scaling**: Independent scaling based on usage
4. **Customization**: Customer-specific configurations and features

### Deployment Architecture

```
Customer A (acme.your-domain.com)
├── Database KB: kb-acme-db-001
├── Support KB: kb-acme-support-001
└── Product KB: kb-acme-product-001

Customer B (techstart.your-domain.com)
├── Database KB: kb-techstart-db-002
└── Support KB: kb-techstart-support-002

Customer C (retail.your-domain.com)
├── Database KB: kb-retail-db-003
└── Product KB: kb-retail-product-003
```

## 📋 Deployment Instructions

### 1. **Configure Customers**

Edit `infrastructure/customer_configs.yaml`:

```yaml
customers:
  - name: "Your Customer Name"
    company_code: "CUST001"
    database_kb_id: "kb-customer-db-001"
    support_kb_id: "kb-customer-support-001"  # Optional
    product_kb_id: "kb-customer-product-001"  # Optional
    subdomain: "customer"
    industry: "Technology"
```

### 2. **Deploy Shared Infrastructure**

First, deploy the shared infrastructure (VPC, ALB, ECR, etc.):

```bash
cd infrastructure
pulumi up
```

### 3. **Deploy Customer-Specific APIs**

Deploy APIs for each customer:

```bash
# List available customers
python deploy_customer.py --list

# Deploy specific customer
python deploy_customer.py CUST001

# Generate example URLs
python deploy_customer.py --urls
```

### 4. **Build and Push Container Images**

```bash
# Build the container
docker build -t dbkb-api .

# Tag for ECR
docker tag dbkb-api:latest [ECR-REPO-URL]:latest

# Push to ECR
docker push [ECR-REPO-URL]:latest
```

### 5. **Update ECS Services**

After pushing new container images, update ECS services:

```bash
aws ecs update-service \
  --cluster dbkb-cluster \
  --service dbkb-acme-service \
  --force-new-deployment
```

## 🔧 Configuration Management

### Environment Variables

Each deployment supports these environment variables:

- `KNOWLEDGE_BASE_ID` - Primary knowledge base ID
- `CUSTOMER_NAME` - Customer name for logging/identification
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR)
- `AWS_DEFAULT_REGION` - AWS region

### SSM Parameters

Database credentials are stored in SSM:
- `/dbkb/chat/db/username` - Database username
- `/dbkb/chat/db/password` - Database password (SecureString)

Customer-specific parameters can be stored at:
- `/dbkb/[customer-subdomain]/config/*`

## 🛡️ Security Features

### 1. **Network Isolation**
- Each customer gets their own security group
- Database access through approved security groups only
- ALB routing based on subdomain

### 2. **IAM Isolation**
- Separate IAM roles per customer
- Knowledge base access limited to customer's KBs only
- SSM parameter access scoped appropriately

### 3. **Data Isolation**
- Chat history stored with company isolation
- No cross-customer data access
- Audit trails per customer

## 📊 Monitoring and Logging

### CloudWatch Logs
Each customer deployment creates separate log groups:
- `/aws/ecs/dbkb-[customer-subdomain]`

### Metrics
- Response times per knowledge base
- Query classification accuracy
- Usage patterns by KB type

### Health Checks
- `/health` endpoint on each deployment
- ALB health checks with 30-second intervals
- Automatic unhealthy target removal

## 🔄 Maintenance and Updates

### 1. **Rolling Updates**
```bash
# Update all customer deployments
for customer in ACME001 TECH002 RETAIL003; do
  python deploy_customer.py $customer
done
```

### 2. **Blue-Green Deployments**
- Deploy new version to new target group
- Test with limited traffic
- Switch ALB routing when ready

### 3. **Scaling**
```bash
# Scale specific customer deployment
aws ecs update-service \
  --cluster dbkb-cluster \
  --service dbkb-[customer]-service \
  --desired-count 3
```

## 🚨 Troubleshooting

### Common Issues:

1. **Knowledge Base Access Denied**
   - Check IAM role permissions
   - Verify knowledge base ID is correct
   - Ensure region matches

2. **Database Connection Failed**
   - Verify security group rules
   - Check SSM parameters
   - Confirm Aurora endpoint accessibility

3. **ALB Routing Issues**
   - Check listener rules priority
   - Verify subdomain DNS configuration
   - Confirm target group health

### Debug Commands:

```bash
# Check ECS service status
aws ecs describe-services --cluster dbkb-cluster --services dbkb-[customer]-service

# View container logs
aws logs tail /aws/ecs/dbkb-[customer] --follow

# Test health endpoint
curl https://[customer].your-domain.com/health
```

## 📈 Performance Optimization

### 1. **Knowledge Base Optimization**
- Use appropriate chunk sizes for different content types
- Optimize embedding models for domain-specific content
- Regular reindexing of updated content

### 2. **API Performance**
- Enable response caching for common queries
- Use connection pooling for database access
- Implement query result caching

### 3. **Infrastructure Scaling**
- Monitor CPU/memory usage per customer
- Auto-scaling based on request volume
- Consider reserved capacity for high-usage customers

## 🔮 Future Enhancements

1. **Advanced Query Routing**
   - Machine learning-based classification
   - User behavior learning
   - Context-aware routing

2. **Multi-Region Deployments**
   - Customer data residency requirements
   - Disaster recovery
   - Global load balancing

3. **Enhanced Analytics**
   - Query performance analytics
   - Knowledge base effectiveness metrics
   - Customer usage insights

## 📞 Support

For deployment issues or questions:
1. Check CloudWatch logs for specific customer deployment
2. Review ALB access logs for routing issues
3. Use AWS X-Ray for distributed tracing
4. Contact the platform team for infrastructure issues