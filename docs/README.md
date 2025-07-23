# ERP Database Knowledge Base

## Overview
This knowledge base provides comprehensive guidance for querying and understanding your ERP database. It's designed to help business users create effective reports, analyze data, and understand database relationships.

## Quick Start Guide

### For New Users
1. Start with [Database Schema](database_schema/database_schema_documentation.md) to understand your data structure
2. Learn [Basic Query Patterns](query_patterns/basic_patterns/simple_queries.md)
3. Explore [Business Guides](business_guides/) for your specific area

### For Experienced Users
- Jump to [Advanced Patterns](query_patterns/advanced_patterns/complex_joins.md)
- Check [Common Use Cases](query_patterns/common_use_cases/reporting_patterns.md)
- Browse [Business-Specific Guides](business_guides/)

---

## Knowledge Base Structure

### 📊 Database Schema
- **[Database Schema Documentation](database_schema/database_schema_documentation.md)** - Complete database structure and relationships

### 🔍 Query Patterns
- **[Basic Patterns](query_patterns/basic_patterns/)** - Fundamental query techniques
  - [Simple Queries](query_patterns/basic_patterns/simple_queries.md)
- **[Advanced Patterns](query_patterns/advanced_patterns/)** - Complex query techniques  
  - [Complex Joins](query_patterns/advanced_patterns/complex_joins.md)
- **[Common Use Cases](query_patterns/common_use_cases/)** - Proven reporting patterns
  - [Reporting Patterns](query_patterns/common_use_cases/reporting_patterns.md)

### 📈 Business Guides
- **[Order Management](business_guides/order_management.md)** - Order tracking, analysis, and profitability
- **[Customer Management](business_guides/customer_management.md)** - Customer analysis and relationship tracking
- **[Inventory Management](business_guides/inventory_management.md)** - Stock tracking and optimization
- **[Sales Reporting](business_guides/sales_reporting.md)** - Revenue analysis and sales performance
- **[Financial Analysis](business_guides/financial_analysis.md)** - Cost analysis and financial reporting

---

## Key Database Tables

### Core Business Tables
- **db_order** - Main order information
- **db_orderitem** - Individual items within orders  
- **db_customer** - Customer master data
- **db_product** - Product catalog
- **db_stock** - Inventory data

### Support Tables  
- **db_vendor** - Vendor information
- **db_salesperson** - Sales team data
- **db_status** - Status codes and descriptions

*See [Database Schema Documentation](database_schema/database_schema_documentation.md) for complete table reference.*

---

## Common Query Examples

### Get Customer Orders
```sql
SELECT 
    o.Wo as OrderNumber,
    c.Name as CustomerName,
    o.Date as OrderDate,
    o.Total as OrderTotal
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
WHERE o.Date >= '2025-01-01'
ORDER BY o.Date DESC;
```

### Monthly Sales Summary
```sql
SELECT 
    YEAR(Date) as Year,
    MONTH(Date) as Month,
    COUNT(*) as OrderCount,
    SUM(Total) as TotalRevenue
FROM db_order
WHERE Status >= 1
GROUP BY YEAR(Date), MONTH(Date)
ORDER BY Year DESC, Month DESC;
```

### Inventory Status
```sql
SELECT 
    p.Product,
    p.Description,
    SUM(s.Qty) as OnHandQty
FROM db_product p
LEFT JOIN db_stock s ON p.Product = s.Product
GROUP BY p.Product, p.Description
ORDER BY p.Product;
```

---

## Best Practices

### Query Writing
- Always use meaningful column aliases
- Filter large tables with WHERE clauses
- Use table aliases for readability
- Sort results with ORDER BY

### Performance
- Index frequently queried columns
- Limit date ranges for large datasets
- Use appropriate join types
- Filter early in your queries

### Data Quality
- Understand status codes and their meanings
- Check for NULL values in calculations
- Validate date ranges
- Use consistent formatting

---

## Getting Help

### Documentation Hierarchy
1. **Start here**: Business guides for your functional area
2. **Learn patterns**: Query pattern documentation
3. **Understand structure**: Database schema reference
4. **Advanced techniques**: Complex query patterns

### Query Building Process
1. **Identify your goal**: What business question are you answering?
2. **Find relevant tables**: Check schema documentation
3. **Start simple**: Begin with basic patterns
4. **Add complexity**: Layer in joins and calculations
5. **Test and refine**: Verify results make business sense

### Common Issues
- **No results**: Check your filter conditions
- **Too many results**: Add WHERE clauses
- **Wrong totals**: Verify join conditions
- **Slow queries**: Check indexes and date ranges

---

## Version Information
- **Knowledge Base Version**: 2.0
- **Last Updated**: 2025-05-23
- **Database Tables Documented**: 890
- **Query Patterns**: 75+ examples

This knowledge base replaces the previous collection of individual query files with curated, educational content designed to help you understand and effectively query your ERP database.