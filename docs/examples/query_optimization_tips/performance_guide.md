# Query Performance Optimization Guide

## Overview
This guide provides practical tips for writing efficient queries against your ERP database. Fast queries improve user experience and reduce system load.

## Core Performance Principles

### 1. Index Usage
Indexes are your best friend for query performance.

#### Good: Using Indexed Columns
```sql
-- Customer table has index on Customer column
SELECT * FROM db_customer WHERE Customer = 'CUST001';

-- Order table has index on Date column  
SELECT * FROM db_order WHERE Date >= '2025-01-01';
```

#### Bad: Avoiding Index Usage
```sql
-- Functions prevent index usage
SELECT * FROM db_order WHERE YEAR(Date) = 2025;

-- Leading wildcards prevent index usage
SELECT * FROM db_customer WHERE Name LIKE '%Smith%';
```

#### Better Alternatives
```sql
-- Use date ranges instead of functions
SELECT * FROM db_order WHERE Date >= '2025-01-01' AND Date < '2026-01-01';

-- Use trailing wildcards when possible
SELECT * FROM db_customer WHERE Name LIKE 'Smith%';
```

---

### 2. Effective Filtering

#### Filter Early and Often
```sql
-- Good: Filter before joining
SELECT o.Wo, c.Name, o.Total
FROM (
    SELECT Wo, Customer, Total 
    FROM db_order 
    WHERE Date >= '2025-01-01' AND Status = 1
) o
JOIN db_customer c ON o.Customer = c.Customer;

-- Better: Use WHERE clause to filter
SELECT o.Wo, c.Name, o.Total
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
WHERE o.Date >= '2025-01-01' AND o.Status = 1;
```

#### Use Specific Conditions
```sql
-- Vague: Scans many records
SELECT * FROM db_order WHERE Total > 1000;

-- Specific: Narrows down quickly
SELECT * FROM db_order 
WHERE Date BETWEEN '2025-01-01' AND '2025-01-31'
  AND Status = 1
  AND Total > 1000;
```

---

### 3. Join Optimization

#### Use Appropriate Join Types
```sql
-- INNER JOIN: Only matching records (fastest)
SELECT o.Wo, c.Name
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer;

-- LEFT JOIN: All left records + matches (slower)
SELECT o.Wo, COALESCE(c.Name, 'Unknown') as CustomerName
FROM db_order o
LEFT JOIN db_customer c ON o.Customer = c.Customer;
```

#### Join on Indexed Columns
```sql
-- Good: Join on primary/foreign keys
SELECT o.Wo, c.Name
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer;  -- Both columns indexed

-- Avoid: Join on non-indexed columns
SELECT o.Wo, c.Name  
FROM db_order o
JOIN db_customer c ON o.CustomerName = c.Name;  -- Name might not be indexed
```

#### Order Joins by Size
```sql
-- Start with smallest table, join to larger ones
SELECT small.id, medium.name, large.description
FROM small_table small
JOIN medium_table medium ON small.id = medium.small_id
JOIN large_table large ON medium.id = large.medium_id;
```

---

### 4. Subquery vs JOIN Performance

#### Subqueries Can Be Slower
```sql
-- Slower: Correlated subquery
SELECT c.Name
FROM db_customer c
WHERE EXISTS (
    SELECT 1 FROM db_order o 
    WHERE o.Customer = c.Customer 
    AND o.Date >= '2025-01-01'
);
```

#### JOINs Are Usually Faster
```sql
-- Faster: Use DISTINCT with JOIN
SELECT DISTINCT c.Name
FROM db_customer c
JOIN db_order o ON c.Customer = o.Customer
WHERE o.Date >= '2025-01-01';
```

#### When Subqueries Are Better
```sql
-- Good use: Aggregation in subquery
SELECT c.Name, order_stats.OrderCount, order_stats.TotalRevenue
FROM db_customer c
JOIN (
    SELECT Customer, COUNT(*) as OrderCount, SUM(Total) as TotalRevenue
    FROM db_order
    WHERE Date >= '2025-01-01'
    GROUP BY Customer
) order_stats ON c.Customer = order_stats.Customer;
```

---

### 5. LIMIT and Pagination

#### Always Use LIMIT for Testing
```sql
-- Test with small result set first
SELECT * FROM db_order 
WHERE Date >= '2025-01-01'
ORDER BY Date DESC
LIMIT 10;
```

#### Implement Pagination Efficiently
```sql
-- Good: Offset pagination (for small offsets)
SELECT * FROM db_order 
ORDER BY Date DESC 
LIMIT 20 OFFSET 100;

-- Better: Cursor-based pagination (for large offsets)
SELECT * FROM db_order 
WHERE Date < '2025-03-15 10:30:00'  -- Last seen date
ORDER BY Date DESC 
LIMIT 20;
```

---

### 6. Aggregation Optimization

#### Use Covering Indexes
```sql
-- If index exists on (Customer, Date, Total)
SELECT Customer, COUNT(*), SUM(Total)
FROM db_order
WHERE Date >= '2025-01-01'
GROUP BY Customer;
```

#### Pre-filter Before Aggregating
```sql
-- Good: Filter then aggregate
SELECT Customer, COUNT(*), AVG(Total)
FROM db_order
WHERE Date >= '2025-01-01' AND Status = 1  -- Filter first
GROUP BY Customer;
```

#### Use HAVING Appropriately
```sql
-- HAVING is for post-aggregation filtering
SELECT Customer, COUNT(*) as OrderCount
FROM db_order
WHERE Date >= '2025-01-01'  -- Pre-aggregation filter
GROUP BY Customer
HAVING COUNT(*) > 5;        -- Post-aggregation filter
```

---

## Query Analysis Tools

### Use EXPLAIN to Understand Execution
```sql
EXPLAIN SELECT o.Wo, c.Name, o.Total
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
WHERE o.Date >= '2025-01-01';
```

### Look for These Red Flags
- **Full table scans** on large tables
- **No index usage** on WHERE/JOIN columns
- **High row examination** ratios
- **Temporary tables** in complex queries

---

## Common Performance Anti-Patterns

### 1. SELECT * in Production
```sql
-- Bad: Returns unnecessary data
SELECT * FROM db_order WHERE Date >= '2025-01-01';

-- Good: Select only needed columns
SELECT Wo, Customer, Date, Total FROM db_order WHERE Date >= '2025-01-01';
```

### 2. Function Calls in WHERE
```sql
-- Bad: Prevents index usage
WHERE UPPER(CustomerName) = 'SMITH';
WHERE YEAR(OrderDate) = 2025;

-- Good: Index-friendly conditions
WHERE CustomerName = 'Smith';  -- Assuming case-insensitive collation
WHERE OrderDate >= '2025-01-01' AND OrderDate < '2026-01-01';
```

### 3. Unnecessary JOINs
```sql
-- Bad: Joining tables not used in output
SELECT o.Wo, o.Total
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer  -- Not needed
JOIN db_product p ON o.Product = p.Product     -- Not needed
WHERE o.Date >= '2025-01-01';

-- Good: Only join what you need
SELECT Wo, Total
FROM db_order
WHERE Date >= '2025-01-01';
```

### 4. Inefficient OR Conditions
```sql
-- Slow: OR conditions
WHERE Customer = 'CUST001' OR Customer = 'CUST002' OR Customer = 'CUST003';

-- Faster: Use IN
WHERE Customer IN ('CUST001', 'CUST002', 'CUST003');
```

---

## Performance Testing Checklist

### Before Deploying Queries
- [ ] Test with realistic data volumes
- [ ] Check execution time with EXPLAIN
- [ ] Verify index usage
- [ ] Test with different parameter values
- [ ] Consider peak usage scenarios

### Monitoring Production Performance
- [ ] Set up slow query logging
- [ ] Monitor frequently run reports
- [ ] Track query response times
- [ ] Review index usage statistics
- [ ] Plan for data growth

---

## Database-Specific Tips

### Index Maintenance
- **Monitor index usage**: Remove unused indexes
- **Update statistics**: Keep query planner informed
- **Consider composite indexes**: For multi-column WHERE clauses

### Connection Management
- **Use connection pooling**: Reduce connection overhead
- **Limit concurrent queries**: Prevent resource contention
- **Close connections**: Free resources promptly

### Data Volume Considerations
- **Archive old data**: Keep active tables smaller
- **Partition large tables**: Improve query performance
- **Consider materialized views**: For complex aggregations

Remember: **Measure before optimizing**. Use actual execution plans and timing data to identify real bottlenecks rather than guessing.