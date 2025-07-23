# Manual VPC Fix Steps

Since there's an issue with the automated script, here are the manual steps to fix the VPC deployment:

## Step 1: Navigate to Infrastructure Directory
```bash
cd /Volumes/Code/dbkb/infrastructure
```

## Step 2: Check Current Stack State
```bash
pulumi stack ls
pulumi stack select dev  # or your stack name
```

## Step 3: Remove ECS Resources in Wrong VPC
Remove the resources in the correct order to avoid dependency issues:

```bash
# Remove ECS Service first
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:ecs/service:Service::dbkb-service --yes

# Remove Load Balancer dependencies
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:lb/listener:Listener::dbkb-https-listener --yes
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:lb/listener:Listener::dbkb-http-listener --yes

# Remove Target Group
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:lb/targetGroup:TargetGroup::dbkb-tg --yes

# Remove Load Balancer
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:lb/loadBalancer:LoadBalancer::dbkb-alb --yes

# Remove Security Groups
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:ec2/securityGroup:SecurityGroup::dbkb-ecs-sg --yes
pulumi destroy --target urn:pulumi:dev::dbkb-infrastructure::aws:ec2/securityGroup:SecurityGroup::dbkb-alb-sg --yes
```

## Step 4: Verify Infrastructure Code Changes
Ensure the infrastructure code is using the correct VPC:

```bash
# Check that the infrastructure file has been updated
grep -n "vpc-f93ec29f" __main__.py
grep -n "target_vpc" __main__.py
```

You should see:
```python
target_vpc = aws.ec2.get_vpc(id="vpc-f93ec29f")
```

## Step 5: Redeploy with Correct VPC
```bash
pulumi up --yes
```

## Step 6: Verify Deployment
```bash
# Check outputs
pulumi stack output alb_dns_name
pulumi stack output ecs_security_group_id

# Test health endpoint
ALB_DNS=$(pulumi stack output alb_dns_name)
curl -k "https://$ALB_DNS/health"
```

## Step 7: Verify VPC Configuration
```bash
# Get ECS security group ID
ECS_SG_ID=$(pulumi stack output ecs_security_group_id)

# Verify it's in the correct VPC
aws ec2 describe-security-groups --group-ids $ECS_SG_ID --query 'SecurityGroups[0].VpcId'
# Should return: "vpc-f93ec29f"

# Verify database security group rules
aws ec2 describe-security-groups --group-ids sg-94cf59e9 --query 'SecurityGroups[0].IpPermissions'
```

## Alternative: Complete Destroy and Recreate
If you encounter issues with selective destruction:

```bash
# Complete destroy
pulumi destroy --yes

# Recreate everything
pulumi up --yes
```

## Verification Checklist
- [ ] ECS tasks are in VPC vpc-f93ec29f
- [ ] ALB is in VPC vpc-f93ec29f  
- [ ] Security groups are in VPC vpc-f93ec29f
- [ ] Database security group rules are working
- [ ] Health endpoint responds successfully
- [ ] API endpoints are accessible

## Expected Results
After fixing the VPC configuration:
- All resources will be in vpc-f93ec29f (same as database)
- Security group rules will work without cross-VPC errors
- Database connectivity will be automatic
- No manual security group configuration needed