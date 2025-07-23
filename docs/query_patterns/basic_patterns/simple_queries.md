# Basic SQL Query Patterns

## Overview
These are fundamental query patterns that every ERP user should know. Start here to understand the basics of querying your database effectively.

## Pattern 1: Simple Data Retrieval

### Purpose
Get basic information from a single table.

### Example: List All Customers
```sql
SELECT Customer, Name, Phone, Email
FROM db_customer
WHERE Status = 'Active'
ORDER BY Name;
```

### Key Concepts
- **SELECT**: Choose which columns to display
- **FROM**: Specify the source table
- **WHERE**: Filter results based on conditions
- **ORDER BY**: Sort the results

### When to Use
- Quick lookups
- Data verification
- Simple reports

---

## Pattern 2: Basic Filtering

### Purpose
Find specific records based on criteria.

### Example: Orders from Last Month
```sql
SELECT Wo, Customer, Date, Total
FROM db_order
WHERE Date >= '2025-04-01' 
  AND Date < '2025-05-01'
  AND Status = 1
ORDER BY Date DESC;
```

### Key Concepts
- **Date filtering**: Use proper date formats
- **Multiple conditions**: Combine with AND/OR
- **Status codes**: Understand what they mean

### When to Use
- Time-based reports
- Status tracking
- Data analysis

---

## Pattern 3: Basic Aggregation

### Purpose
Calculate totals, counts, and averages.

### Example: Order Summary by Month
```sql
SELECT 
    YEAR(Date) as Year,
    MONTH(Date) as Month,
    COUNT(*) as OrderCount,
    SUM(Total) as TotalRevenue,
    AVG(Total) as AverageOrderValue
FROM db_order
WHERE Status >= 1
GROUP BY YEAR(Date), MONTH(Date)
ORDER BY Year DESC, Month DESC;
```

### Key Concepts
- **COUNT(*)**: Count all rows
- **SUM()**: Add up values
- **AVG()**: Calculate averages
- **GROUP BY**: Group data for aggregation

### When to Use
- Summary reports
- Performance metrics
- Trend analysis

---

## Pattern 4: Simple Joins

### Purpose
Combine data from related tables.

### Example: Orders with Customer Names
```sql
SELECT 
    o.Wo,
    o.Date,
    c.Name as CustomerName,
    o.Total
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
WHERE o.Date >= '2025-01-01'
ORDER BY o.Date DESC;
```

### Key Concepts
- **JOIN**: Connect related tables
- **ON**: Specify the relationship
- **Table aliases**: Use short names (o, c)

### When to Use
- Readable reports
- Data relationships
- Most real-world queries

---

## Best Practices for Basic Queries

1. **Always use meaningful column names**
   ```sql
   SELECT Name as CustomerName, Phone as ContactPhone
   ```

2. **Filter early and often**
   ```sql
   WHERE Status = 'Active' AND Date >= '2025-01-01'
   ```

3. **Use table aliases for clarity**
   ```sql
   FROM db_order o JOIN db_customer c
   ```

4. **Sort your results**
   ```sql
   ORDER BY Date DESC, CustomerName
   ```

5. **Comment complex conditions**
   ```sql
   WHERE Status = 1  -- Active orders only
   ```

## Common Mistakes to Avoid

- **Missing WHERE clauses**: Always filter large tables
- **Wrong date formats**: Use 'YYYY-MM-DD' format
- **Forgetting ORDER BY**: Results may appear random
- **Not using aliases**: Makes queries hard to read