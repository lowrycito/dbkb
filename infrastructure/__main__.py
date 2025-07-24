#!/usr/bin/env python3
"""
Pulumi infrastructure for Database Knowledge Base (DBKB) ECS Fargate deployment
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, Output

# Get configuration
config = Config()
knowledge_base_id = config.get("knowledge-base-id") or "KRD3MW7QFS"
region = config.get("aws:region") or "us-east-1"

# Create an ECR repository for our container
ecr_repository = aws.ecr.Repository(
    "dbkb-repository",
    name="dbkb-api",
    image_tag_mutability="MUTABLE",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
    encryption_configurations=[aws.ecr.RepositoryEncryptionConfigurationArgs(
        encryption_type="AES256",
    )],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create IAM role for ECS Tasks (with Bedrock permissions)
ecs_task_role = aws.iam.Role(
    "dbkb-ecs-task-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }""",
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create IAM policy for Bedrock access
bedrock_policy = aws.iam.Policy(
    "dbkb-bedrock-policy",
    policy=pulumi.Output.all(knowledge_base_id, region).apply(lambda args: f"""{{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                    "bedrock-runtime:InvokeModel",
                    "bedrock-runtime:Retrieve",
                    "bedrock-runtime:RetrieveAndGenerate",
                    "bedrock-agent:*",
                    "bedrock-agent-runtime:*"
                ],
                "Resource": [
                    "arn:aws:bedrock:{args[1]}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                    "arn:aws:bedrock:{args[1]}::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0",
                    "arn:aws:bedrock:{args[1]}::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:{args[1]}::inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0",
                    "arn:aws:bedrock:{args[1]}:*:knowledge-base/{args[0]}",
                    "arn:aws:bedrock:{args[1]}:*:knowledge-base/{args[0]}/*"
                ]
            }},
            {{
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation"
                ],
                "Resource": "*"
            }},
            {{
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath"
                ],
                "Resource": [
                    "arn:aws:ssm:{args[1]}:*:parameter/dbkb/chat/db/*"
                ]
            }},
            {{
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }}
        ]
    }}"""),
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Attach the policy to the role
policy_attachment = aws.iam.RolePolicyAttachment(
    "dbkb-policy-attachment",
    role=ecs_task_role.name,
    policy_arn=bedrock_policy.arn
)


# Get current AWS account ID for ECR image URI
current_identity = aws.get_caller_identity()

# CloudWatch Log Group for ECS
log_group = aws.cloudwatch.LogGroup(
    "dbkb-ecs-logs",
    name="/aws/ecs/dbkb-api",
    retention_in_days=30,
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Get the correct VPC where the database is located
target_vpc = aws.ec2.get_vpc(id="vpc-f93ec29f")
target_subnets = aws.ec2.get_subnets(filters=[
    aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[target_vpc.id])
])

# Create ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    "dbkb-cluster",
    name="dbkb-cluster",
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create Security Group for ALB
alb_security_group = aws.ec2.SecurityGroup(
    "dbkb-alb-sg",
    name="dbkb-alb-sg",
    description="Security group for DBKB Application Load Balancer",
    vpc_id=target_vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"]
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create Application Load Balancer
alb = aws.lb.LoadBalancer(
    "dbkb-alb",
    name="dbkb-alb",
    load_balancer_type="application",
    internal=False,  # internet-facing
    subnets=target_subnets.ids,
    security_groups=[alb_security_group.id],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create Target Group
target_group = aws.lb.TargetGroup(
    "dbkb-tg",
    name="dbkb-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=target_vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200",
        path="/health",
        port="traffic-port",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=2
    ),
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Get default ACM certificate (you may need to create one)
# For now, we'll create a self-signed cert or use the default AWS one
# In production, you should use a proper domain with ACM certificate

# Create HTTP Listener (redirects to HTTPS)
http_listener = aws.lb.Listener(
    "dbkb-http-listener",
    load_balancer_arn=alb.arn,
    port="80",
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="redirect",
        redirect=aws.lb.ListenerDefaultActionRedirectArgs(
            port="443",
            protocol="HTTPS",
            status_code="HTTP_301"
        )
    )]
)

# Create HTTPS Listener
# Note: This requires an SSL certificate. For demo purposes, we'll use AWS's default
# In production, you should use AWS Certificate Manager with your domain
https_listener = aws.lb.Listener(
    "dbkb-https-listener",
    load_balancer_arn=alb.arn,
    port="443",
    protocol="HTTPS",
    ssl_policy="ELBSecurityPolicy-TLS-1-2-2017-01",
    certificate_arn="arn:aws:acm:us-east-1:836255806547:certificate/9eb0536b-380c-4ebb-8ce6-a33f88df0b0d",  # *.picbusiness.com wildcard cert
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=target_group.arn
    )]
)

# Create Security Group for ECS tasks
ecs_security_group = aws.ec2.SecurityGroup(
    "dbkb-ecs-sg",
    name="dbkb-ecs-sg",
    description="Security group for DBKB ECS tasks",
    vpc_id=target_vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[alb_security_group.id]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Add database security group rules for Aurora access (now in same VPC)
ecs_to_db_rule = aws.ec2.SecurityGroupRule(
    "dbkb-ecs-to-db-rule",
    type="egress",
    from_port=3306,
    to_port=3306,
    protocol="tcp",
    source_security_group_id="sg-94cf59e9",  # Database security group
    security_group_id=ecs_security_group.id,
    description="Allow ECS tasks to access Aurora MySQL database"
)

# Add rule to database security group to allow access from ECS
db_from_ecs_rule = aws.ec2.SecurityGroupRule(
    "dbkb-db-from-ecs-rule",
    type="ingress",
    from_port=3306,
    to_port=3306,
    protocol="tcp",
    source_security_group_id=ecs_security_group.id,
    security_group_id="sg-94cf59e9",  # Database security group
    description="Allow access from DBKB ECS tasks to Aurora MySQL"
)

# Update IAM role for ECS task execution
task_execution_role = aws.iam.Role(
    "dbkb-task-execution-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }""",
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
    ],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create ECS Task Definition
task_definition = aws.ecs.TaskDefinition(
    "dbkb-task",
    family="dbkb-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    runtime_platform=aws.ecs.TaskDefinitionRuntimePlatformArgs(
        cpu_architecture="ARM64",
        operating_system_family="LINUX"
    ),
    execution_role_arn=task_execution_role.arn,
    task_role_arn=ecs_task_role.arn,  # Reuse the existing role with Bedrock permissions
    container_definitions=pulumi.Output.all(
        ecr_repository.repository_url,
        knowledge_base_id,
        region,
        log_group.name
    ).apply(lambda args: f"""[
        {{
            "name": "dbkb-container",
            "image": "{args[0]}:latest",
            "portMappings": [
                {{
                    "containerPort": 8000,
                    "protocol": "tcp"
                }}
            ],
            "environment": [
                {{
                    "name": "KNOWLEDGE_BASE_ID",
                    "value": "{args[1]}"
                }},
                {{
                    "name": "LOG_LEVEL",
                    "value": "INFO"
                }},
                {{
                    "name": "AWS_DEFAULT_REGION",
                    "value": "{args[2]}"
                }}
            ],
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{args[3]}",
                    "awslogs-region": "{args[2]}",
                    "awslogs-stream-prefix": "ecs"
                }}
            }},
            "essential": true
        }}
    ]"""),
    tags={
        "Project": "DBKB",
        "Environment": "production"
    }
)

# Create ECS Service
ecs_service = aws.ecs.Service(
    "dbkb-service",
    name="dbkb-service",
    cluster=ecs_cluster.id,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=target_subnets.ids,
        security_groups=[ecs_security_group.id],
        assign_public_ip=True
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=target_group.arn,
        container_name="dbkb-container",
        container_port=8000
    )],
    tags={
        "Project": "DBKB",
        "Environment": "production"
    },
    opts=pulumi.ResourceOptions(
        depends_on=[https_listener, http_listener, policy_attachment]
    )
)

# Output important values
pulumi.export("ecr_repository_url", ecr_repository.repository_url)
pulumi.export("ecr_repository_name", ecr_repository.name)
pulumi.export("ecs_cluster_name", ecs_cluster.name)
pulumi.export("ecs_security_group_id", ecs_security_group.id)
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_hosted_zone_id", alb.zone_id)
pulumi.export("task_role_arn", ecs_task_role.arn)
pulumi.export("task_execution_role_arn", task_execution_role.arn)

# Export configuration
pulumi.export("knowledge_base_id", knowledge_base_id)
pulumi.export("aws_region", region)

# API endpoints for easy access (HTTPS only)
pulumi.export("api_health_endpoint", alb.dns_name.apply(lambda dns: f"https://{dns}/health"))
pulumi.export("api_query_endpoint", alb.dns_name.apply(lambda dns: f"https://{dns}/query"))
pulumi.export("api_docs_endpoint", alb.dns_name.apply(lambda dns: f"https://{dns}/docs"))
pulumi.export("api_base_url", alb.dns_name.apply(lambda dns: f"https://{dns}"))
