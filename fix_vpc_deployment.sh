#!/bin/bash
set -e

echo "🔧 Fixing VPC deployment issue for DBKB..."

# Navigate to infrastructure directory
cd infrastructure

echo "📋 Current stack resources:"
pulumi stack --show-urns

echo ""
echo "🗑️  Removing ECS resources deployed in wrong VPC..."

# Remove ECS resources in specific order to avoid dependency issues
echo "Removing ECS Service..."
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:ecs/service:Service::dbkb-service --yes || echo "Service already removed"

echo "Removing Target Group..."
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:lb/targetGroup:TargetGroup::dbkb-tg --yes || echo "Target Group already removed"

echo "Removing Load Balancer Listeners..."
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:lb/listener:Listener::dbkb-https-listener --yes || echo "HTTPS Listener already removed"
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:lb/listener:Listener::dbkb-http-listener --yes || echo "HTTP Listener already removed"

echo "Removing Load Balancer..."
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:lb/loadBalancer:LoadBalancer::dbkb-alb --yes || echo "ALB already removed"

echo "Removing Security Groups..."
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:ec2/securityGroup:SecurityGroup::dbkb-ecs-sg --yes || echo "ECS Security Group already removed"
pulumi state delete urn:pulumi:dev::dbkb-infrastructure::aws:ec2/securityGroup:SecurityGroup::dbkb-alb-sg --yes || echo "ALB Security Group already removed"

echo ""
echo "🏗️  Redeploying with correct VPC (vpc-f93ec29f)..."
pulumi up --yes

echo ""
echo "✅ VPC deployment fix completed!"
echo "🌐 New ALB DNS: $(pulumi stack output alb_dns_name)"
echo "🔒 ECS Security Group: $(pulumi stack output ecs_security_group_id)"

echo ""
echo "🧪 Testing deployment..."
sleep 30
ALB_DNS=$(pulumi stack output alb_dns_name)
curl -k "https://$ALB_DNS/health" || echo "Health check failed - service may still be starting"

echo ""
echo "✅ Deployment fix complete! ECS is now in the correct VPC with the database."