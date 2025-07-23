#!/usr/bin/env python3
"""
Pulumi infrastructure for per-Knowledge Base API deployments
This allows deploying separate API instances for different knowledge bases
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, Output

def create_kb_specific_infrastructure(kb_id: str, customer_name: str, config: Config):
    """Create infrastructure for a specific knowledge base"""
    
    # Sanitize names for AWS resources
    safe_customer_name = customer_name.lower().replace(' ', '-').replace('_', '-')
    resource_prefix = f"dbkb-{safe_customer_name}"
    
    # Create IAM role for this specific KB
    kb_role = aws.iam.Role(
        f"{resource_prefix}-role",
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
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    # Create KB-specific IAM policy
    kb_policy = aws.iam.Policy(
        f"{resource_prefix}-policy",
        policy=Output.all(kb_id, config.get("aws:region")).apply(lambda args: f"""{{
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
                        "arn:aws:ssm:{args[1]}:*:parameter/dbkb/chat/db/*",
                        "arn:aws:ssm:{args[1]}:*:parameter/dbkb/{safe_customer_name}/*"
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
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    # Attach policy to role
    policy_attachment = aws.iam.RolePolicyAttachment(
        f"{resource_prefix}-policy-attachment",
        role=kb_role.name,
        policy_arn=kb_policy.arn
    )
    
    # Get shared infrastructure (VPC, ALB, etc.)
    default_vpc = aws.ec2.get_vpc(default=True)
    default_subnets = aws.ec2.get_subnets(filters=[
        aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[default_vpc.id])
    ])
    
    # Get existing ALB (created by main infrastructure)
    existing_alb = aws.lb.get_load_balancer(name="dbkb-alb")
    
    # Create target group for this KB
    target_group = aws.lb.TargetGroup(
        f"{resource_prefix}-tg",
        name=f"{resource_prefix}-tg"[:32],  # ALB target group names limited to 32 chars
        port=8000,
        protocol="HTTP",
        vpc_id=default_vpc.id,
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
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    # Create listener rule for customer-specific subdomain
    listener_rule = aws.lb.ListenerRule(
        f"{resource_prefix}-listener-rule",
        listener_arn=f"{existing_alb.arn.apply(lambda arn: arn + ':443')}",
        priority=100,  # You may need to manage priorities manually
        conditions=[
            aws.lb.ListenerRuleConditionArgs(
                host_header=aws.lb.ListenerRuleConditionHostHeaderArgs(
                    values=[f"{safe_customer_name}.your-domain.com"]
                )
            )
        ],
        actions=[
            aws.lb.ListenerRuleActionArgs(
                type="forward",
                target_group_arn=target_group.arn
            )
        ]
    )
    
    # Create security group for this KB's ECS tasks
    ecs_security_group = aws.ec2.SecurityGroup(
        f"{resource_prefix}-ecs-sg",
        name=f"{resource_prefix}-ecs-sg",
        description=f"Security group for {customer_name} DBKB ECS tasks",
        vpc_id=default_vpc.id,
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=8000,
                to_port=8000,
                cidr_blocks=["0.0.0.0/0"]  # ALB will filter
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
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    # Add database access rules
    db_access_rule = aws.ec2.SecurityGroupRule(
        f"{resource_prefix}-db-access",
        type="egress",
        from_port=3306,
        to_port=3306,
        protocol="tcp",
        source_security_group_id="sg-94cf59e9",
        security_group_id=ecs_security_group.id,
        description=f"Allow {customer_name} ECS tasks to access Aurora MySQL"
    )
    
    # Log group for this KB
    log_group = aws.cloudwatch.LogGroup(
        f"{resource_prefix}-logs",
        name=f"/aws/ecs/{resource_prefix}",
        retention_in_days=30,
        tags={
            "Project": "DBKB",
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    return {
        "role": kb_role,
        "policy": kb_policy,
        "target_group": target_group,
        "security_group": ecs_security_group,
        "log_group": log_group,
        "listener_rule": listener_rule
    }

def create_kb_ecs_service(kb_id: str, customer_name: str, infrastructure: dict, config: Config):
    """Create ECS service for a specific knowledge base"""
    
    safe_customer_name = customer_name.lower().replace(' ', '-').replace('_', '-')
    resource_prefix = f"dbkb-{safe_customer_name}"
    
    # Get shared infrastructure
    ecs_cluster = aws.ecs.get_cluster(cluster_name="dbkb-cluster")
    ecr_repository = aws.ecr.get_repository(name="dbkb-api")
    
    # Task execution role (shared)
    task_execution_role = aws.iam.get_role(name="dbkb-task-execution-role")
    
    # Create task definition for this KB
    task_definition = aws.ecs.TaskDefinition(
        f"{resource_prefix}-task",
        family=f"{resource_prefix}-task",
        cpu="256",
        memory="512",
        network_mode="awsvpc",
        requires_compatibilities=["FARGATE"],
        runtime_platform=aws.ecs.TaskDefinitionRuntimePlatformArgs(
            cpu_architecture="ARM64",
            operating_system_family="LINUX"
        ),
        execution_role_arn=task_execution_role.arn,
        task_role_arn=infrastructure["role"].arn,
        container_definitions=Output.all(
            ecr_repository.repository_url,
            kb_id,
            config.get("aws:region"),
            infrastructure["log_group"].name
        ).apply(lambda args: f"""[
            {{
                "name": "{resource_prefix}-container",
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
                        "name": "CUSTOMER_NAME",
                        "value": "{customer_name}"
                    }},
                    {{
                        "name": "LOG_LEVEL",
                        "value": "INFO"
                    }},
                    {{
                        "name": "AWS_DEFAULT_REGION",
                        "value": "{args[3]}"
                    }}
                ],
                "logConfiguration": {{
                    "logDriver": "awslogs",
                    "options": {{
                        "awslogs-group": "{args[3]}",
                        "awslogs-region": "{args[3]}",
                        "awslogs-stream-prefix": "ecs"
                    }}
                }},
                "essential": true
            }}
        ]"""),
        tags={
            "Project": "DBKB",
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    # Create ECS service
    ecs_service = aws.ecs.Service(
        f"{resource_prefix}-service",
        name=f"{resource_prefix}-service",
        cluster=ecs_cluster.arn,
        task_definition=task_definition.arn,
        desired_count=1,
        launch_type="FARGATE",
        network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
            subnets=[subnet.id for subnet in aws.ec2.get_subnets(filters=[
                aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[aws.ec2.get_vpc(default=True).id])
            ]).ids],
            security_groups=[infrastructure["security_group"].id],
            assign_public_ip=True
        ),
        load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=infrastructure["target_group"].arn,
            container_name=f"{resource_prefix}-container",
            container_port=8000
        )],
        tags={
            "Project": "DBKB",
            "Customer": customer_name,
            "KnowledgeBaseId": kb_id,
            "Environment": "production"
        }
    )
    
    return {
        "task_definition": task_definition,
        "service": ecs_service
    }

# Example usage - you would call this for each customer/KB combination
def deploy_customer_kb(customer_config: dict):
    """Deploy infrastructure for a specific customer's knowledge base"""
    config = Config()
    
    customer_name = customer_config["name"]
    kb_id = customer_config["knowledge_base_id"]
    
    # Create infrastructure
    infrastructure = create_kb_specific_infrastructure(kb_id, customer_name, config)
    
    # Create ECS service
    service = create_kb_ecs_service(kb_id, customer_name, infrastructure, config)
    
    # Export customer-specific outputs
    safe_name = customer_name.lower().replace(' ', '-').replace('_', '-')
    pulumi.export(f"{safe_name}_kb_id", kb_id)
    pulumi.export(f"{safe_name}_role_arn", infrastructure["role"].arn)
    pulumi.export(f"{safe_name}_target_group_arn", infrastructure["target_group"].arn)
    pulumi.export(f"{safe_name}_api_url", f"https://{safe_name}.your-domain.com")
    
    return {
        "infrastructure": infrastructure,
        "service": service
    }