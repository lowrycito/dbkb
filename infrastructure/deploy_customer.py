#!/usr/bin/env python3
"""
Deploy customer-specific DBKB API instances
Usage: python deploy_customer.py [customer_code]
"""

import yaml
import argparse
import sys
from per_kb_deployment import deploy_customer_kb

def load_customer_configs():
    """Load customer configurations from YAML file"""
    try:
        with open('customer_configs.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("Error: customer_configs.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing customer_configs.yaml: {e}")
        sys.exit(1)

def find_customer_config(configs, customer_code):
    """Find customer configuration by company code"""
    for customer in configs['customers']:
        if customer.get('company_code') == customer_code:
            return customer
    return None

def deploy_customer(customer_code):
    """Deploy infrastructure for a specific customer"""
    configs = load_customer_configs()
    customer_config = find_customer_config(configs, customer_code)
    
    if not customer_config:
        print(f"Error: Customer with code '{customer_code}' not found in configuration")
        available_customers = [c.get('company_code') for c in configs['customers']]
        print(f"Available customers: {', '.join(available_customers)}")
        sys.exit(1)
    
    print(f"Deploying DBKB API for {customer_config['name']} ({customer_code})")
    print(f"Database KB: {customer_config['database_kb_id']}")
    
    if customer_config.get('support_kb_id'):
        print(f"Support KB: {customer_config['support_kb_id']}")
    
    if customer_config.get('product_kb_id'):
        print(f"Product KB: {customer_config['product_kb_id']}")
    
    # Deploy using Pulumi
    try:
        result = deploy_customer_kb({
            'name': customer_config['name'],
            'knowledge_base_id': customer_config['database_kb_id'],
            'company_code': customer_config['company_code'],
            'subdomain': customer_config['subdomain'],
            'support_kb_id': customer_config.get('support_kb_id'),
            'product_kb_id': customer_config.get('product_kb_id'),
            'industry': customer_config.get('industry', 'Unknown')
        })
        
        print(f"✅ Successfully deployed {customer_config['name']} API")
        print(f"🌐 API URL: https://{customer_config['subdomain']}.{configs['domain']['base_domain']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

def list_customers():
    """List all available customers"""
    configs = load_customer_configs()
    print("Available customers for deployment:")
    print("-" * 50)
    
    for customer in configs['customers']:
        print(f"Code: {customer.get('company_code')}")
        print(f"Name: {customer['name']}")
        print(f"Industry: {customer.get('industry', 'Unknown')}")
        print(f"Subdomain: {customer['subdomain']}")
        print(f"Database KB: {customer['database_kb_id']}")
        
        if customer.get('support_kb_id'):
            print(f"Support KB: {customer['support_kb_id']}")
        if customer.get('product_kb_id'):
            print(f"Product KB: {customer['product_kb_id']}")
        
        print("-" * 30)

def generate_url_examples():
    """Generate example URLs for all customers"""
    configs = load_customer_configs()
    base_domain = configs['domain']['base_domain']
    
    print("Example URLs for customer access:")
    print("=" * 60)
    
    for customer in configs['customers']:
        subdomain = customer['subdomain']
        company_code = customer.get('company_code')
        db_kb = customer['database_kb_id']
        support_kb = customer.get('support_kb_id', '')
        product_kb = customer.get('product_kb_id', '')
        
        print(f"\n{customer['name']} ({company_code}):")
        print(f"API Base: https://{subdomain}.{base_domain}")
        
        # Generate example URL with parameters
        url_params = [
            f"DatabaseKnowledgeBaseId={db_kb}",
            f"Company={company_code}",
            f"CompanyName={customer['name'].replace(' ', '%20')}",
            f"Industry={customer.get('industry', 'Unknown')}",
            "DatabaseHost=your-db-host",
            "DatabaseSchema=your-schema",
            "LoginId=user123",
            "FirstName=John",
            "LastName=Doe",
            "Email=john.doe@company.com"
        ]
        
        if support_kb:
            url_params.append(f"SupportKnowledgeBaseId={support_kb}")
        
        if product_kb:
            url_params.append(f"ProductKnowledgeBaseId={product_kb}")
        
        example_url = f"https://{subdomain}.{base_domain}/?{'&'.join(url_params)}"
        print(f"Example URL:")
        print(f"  {example_url}")

def main():
    parser = argparse.ArgumentParser(description='Deploy customer-specific DBKB API instances')
    parser.add_argument('customer_code', nargs='?', help='Customer company code (e.g., ACME001)')
    parser.add_argument('--list', action='store_true', help='List all available customers')
    parser.add_argument('--urls', action='store_true', help='Generate example URLs for all customers')
    
    args = parser.parse_args()
    
    if args.list:
        list_customers()
    elif args.urls:
        generate_url_examples()
    elif args.customer_code:
        deploy_customer(args.customer_code)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()