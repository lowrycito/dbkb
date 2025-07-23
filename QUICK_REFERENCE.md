# DBKB Quick Reference Guide

## 🚀 Quick Start

### Deploy Changes
```bash
# Build and deploy in one command
./deploy.sh

# Manual deployment
docker buildx build --platform linux/arm64 -t dbkb-api:latest .
docker tag dbkb-api:latest 836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 836255806547.dkr.ecr.us-east-1.amazonaws.com
docker push 836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api:latest
aws ecs update-service --cluster dbkb-cluster --service dbkb-service --force-new-deployment
```

### Test API
```bash
# Health check
curl -k "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/health"

# Basic query
curl -k -X POST "https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "what tables are in this database?"}'
```

## 📋 Key Information

| Component | Value |
|-----------|-------|
| **Endpoint** | `https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/` |
| **Model** | Claude Sonnet 4 (`us.anthropic.claude-sonnet-4-20250514-v1:0`) |
| **Knowledge Base ID** | `KRD3MW7QFS` |
| **ECS Cluster** | `dbkb-cluster` |
| **ECS Service** | `dbkb-service` |
| **ECR Repository** | `836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api` |
| **IAM Task Role** | `dbkb-app-runner-role-5e37961` |
| **IAM Policy** | `dbkb-bedrock-policy-5c5c903` (v6) |

## 🛠️ Common Commands

### AWS CLI
```bash
# Service status
aws ecs describe-services --cluster dbkb-cluster --services dbkb-service --query 'services[0].{status: status, runningCount: runningCount}'

# View logs
TASK_ID=$(aws ecs list-tasks --cluster dbkb-cluster --service-name dbkb-service --query 'taskArns[0]' | tr -d '"' | xargs basename)
aws logs get-log-events --log-group-name "/aws/ecs/dbkb-api" --log-stream-name "ecs/dbkb-container/$TASK_ID" --query 'events[-10:]'

# Search for errors
aws logs filter-log-events --log-group-name "/aws/ecs/dbkb-api" --filter-pattern "ERROR"
```

### Docker
```bash
# Build ARM64 image
docker buildx build --platform linux/arm64 -t dbkb-api:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 836255806547.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 836255806547.dkr.ecr.us-east-1.amazonaws.com/dbkb-api:latest
```

## 🔧 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/query` | POST | General database queries |
| `/relationship` | POST | Table relationship analysis |
| `/optimize` | POST | SQL query optimization |
| `/` | GET | Web interface |
| `/docs` | GET | API documentation |

### Request Format
```json
{
  "query_text": "your question here",
  "extended_thinking": false,
  "include_contexts": false,
  "include_thinking": false
}
```

## 🏗️ Pipeline Commands

### Extract Schema
```bash
python main.py extract-schema --section postgresql --output schema_data.json --generate-markdown
```

### Analyze Queries
```bash
python main.py analyze-queries --input queries.sql --output query_analysis.json --schema schema_data.json --generate-markdown
```

### Generate Docs
```bash
python main.py generate-docs --schema schema_data.json --queries query_analysis.json --output-dir docs
```

### Upload to S3
```bash
python main.py upload --bucket my-bucket --prefix dbkb --region us-east-1 --create-bucket
```

### Setup Knowledge Base
```bash
python main.py setup-kb --bucket my-bucket --prefix dbkb --region us-east-1 --name "DB Knowledge Base"
```

### Run Complete Pipeline
```bash
python main.py run-all --section postgresql --queries queries.sql --bucket dbkb-bucket --prefix dbkb --region us-east-1 --kb-name "Production DB KB" --create-bucket
```

## 🚨 Troubleshooting

### Service Issues
```bash
# Check deployment status
aws ecs describe-services --cluster dbkb-cluster --services dbkb-service --query 'services[0].deployments[0].rolloutState'

# Force restart
aws ecs update-service --cluster dbkb-cluster --service dbkb-service --desired-count 0
aws ecs update-service --cluster dbkb-cluster --service dbkb-service --desired-count 1
```

### Permission Issues
```bash
# Check IAM policy
aws iam get-policy-version --policy-arn arn:aws:iam::836255806547:policy/dbkb-bedrock-policy-5c5c903 --version-id v6

# Test Bedrock access
aws bedrock-runtime invoke-model --model-id us.anthropic.claude-sonnet-4-20250514-v1:0 --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"test"}]}' output.json
```

### Health Check Failures
```bash
# Check load balancer targets
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:836255806547:targetgroup/dbkb-tg/776726325fad6928

# Direct container test (if port forwarding available)
curl http://localhost:8000/health
```

## 📁 File Structure

```
dbkb/
├── app.py                      # Main FastAPI application
├── main.py                     # Pipeline CLI
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── DEPLOYMENT.md              # Deployment guide
├── API_DOCUMENTATION.md       # API reference
├── PIPELINE_DOCUMENTATION.md  # Pipeline guide
├── src/
│   ├── advanced_retrieval/     # Claude integration
│   ├── schema_extraction/      # Database extraction
│   ├── query_analysis/         # SQL analysis
│   ├── documentation/          # Markdown generation
│   ├── bedrock_setup/          # AWS setup
│   └── ui/                     # Web interface
├── utils/
│   └── retrieval.py           # Utility functions
├── docs/                      # Generated documentation
└── infrastructure/            # Pulumi deployment
```

## 🔑 Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `KNOWLEDGE_BASE_ID` | `KRD3MW7QFS` | Bedrock KB ID |
| `LOG_LEVEL` | `INFO` | Logging level |

## 📊 Monitoring

### Key Metrics
- Response time < 10 seconds
- Error rate < 1%
- Memory usage < 400MB
- CPU usage < 80%

### Alerts Setup
```bash
# CloudWatch alarms
aws cloudwatch put-metric-alarm --alarm-name "DBKB-High-Error-Rate" --alarm-description "High error rate in DBKB API" --metric-name "4XXError" --namespace "AWS/ApplicationELB" --statistic "Sum" --period 300 --threshold 10 --comparison-operator "GreaterThanThreshold"
```

## 🔄 Update Checklist

### Code Changes
- [ ] Update code
- [ ] Test locally
- [ ] Build ARM64 image
- [ ] Push to ECR
- [ ] Deploy to ECS
- [ ] Verify health
- [ ] Test API functionality

### Model Changes
- [ ] Update model ID in code
- [ ] Update IAM permissions
- [ ] Test model access
- [ ] Deploy changes
- [ ] Validate responses

### Pipeline Changes
- [ ] Test pipeline locally
- [ ] Update documentation
- [ ] Run full pipeline
- [ ] Verify KB sync
- [ ] Test API responses

## 📞 Support Contacts

| Issue Type | Resource |
|------------|----------|
| **Deployment** | Check CloudWatch logs `/aws/ecs/dbkb-api` |
| **API Issues** | Test with `/docs` endpoint |
| **Model Issues** | Check Bedrock service status |
| **Pipeline Issues** | Review pipeline logs and S3 sync |

## 🔗 Quick Links

- **API Endpoint**: https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/
- **API Docs**: https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/docs
- **Web Interface**: https://dbkb-alb-493056638.us-east-1.elb.amazonaws.com/
- **CloudWatch Logs**: [ECS Logs](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/%2Faws%2Fecs%2Fdbkb-api)
- **ECS Service**: [ECS Console](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dbkb-cluster/services/dbkb-service)
- **Bedrock KB**: [Bedrock Console](https://console.aws.amazon.com/bedrock/home?region=us-east-1#/knowledge-bases/KRD3MW7QFS)