# SSM Parameter Setup for DBKB Chat Database

## Overview
The DBKB application now retrieves database credentials from AWS Systems Manager (SSM) Parameter Store instead of environment variables for enhanced security.

## Required SSM Parameters

You need to create the following SSM parameters in your AWS account:

### 1. Database Username
```bash
aws ssm put-parameter \
  --name "/dbkb/chat/db/username" \
  --value "your_database_username" \
  --type "String" \
  --description "Username for DBKB chat database" \
  --region us-east-1
```

### 2. Database Password (SecureString)
```bash
aws ssm put-parameter \
  --name "/dbkb/chat/db/password" \
  --value "your_database_password" \
  --type "SecureString" \
  --description "Password for DBKB chat database" \
  --region us-east-1
```

## Security Group Configuration

The infrastructure has been updated to include:

1. **ECS Security Group Access**: The ECS tasks can now access the database security group `sg-94cf59e9`
2. **Database Security Group Rules**: Added ingress rule to `sg-94cf59e9` to allow connections from the ECS security group on port 3306

## IAM Permissions

The ECS task role now includes the following SSM permissions:

```json
{
    "Effect": "Allow",
    "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters", 
        "ssm:GetParametersByPath"
    ],
    "Resource": [
        "arn:aws:ssm:us-east-1:*:parameter/dbkb/chat/db/*"
    ]
}
```

## Database Connection Details

The application connects to:
- **Host**: `dev.writer.pic.picbusiness.aws`
- **Database**: `chat`
- **Port**: `3306` (MySQL)
- **Username**: Retrieved from `/dbkb/chat/db/username`
- **Password**: Retrieved from `/dbkb/chat/db/password`

## Fallback Behavior

If SSM parameters are not available or there's an error retrieving them, the application will fall back to:
- Environment variable `CHAT_DB_USER` (default: 'chat_user')
- Environment variable `CHAT_DB_PASSWORD` (default: '')

## Deployment Instructions

1. **Create SSM Parameters** (as shown above)
2. **Deploy Infrastructure**: Run `pulumi up` in the infrastructure directory
3. **Build and Deploy Container**: The application will automatically use SSM credentials

## Testing

After deployment, you can verify the database connection by:

1. Checking the application logs for successful database connection
2. Testing the chat endpoints with proper URL parameters
3. Verifying chat history persistence

## Security Notes

- The password parameter uses `SecureString` type for encryption at rest
- Only the ECS task role has permission to read these specific parameters
- Database access is restricted to the ECS security group only
- All connections use SSL/TLS encryption