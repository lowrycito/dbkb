# Common Reporting Patterns

## Overview
These are proven query patterns for generating common business reports in your ERP system. Use these templates as starting points for your own reports.

## Pattern 1: Time-Based Sales Reports

### Purpose
Generate sales reports grouped by time periods (daily, weekly, monthly, yearly).

### Example: Monthly Sales Summary
```sql
SELECT 
    YEAR(o.Date) as Year,
    MONTH(o.Date) as Month,
    MONTHNAME(o.Date) as MonthName,
    COUNT(DISTINCT o.Wo) as OrderCount,
    COUNT(DISTINCT o.Customer) as UniqueCustomers,
    SUM(o.Total) as TotalRevenue,
    AVG(o.Total) as AverageOrderValue,
    SUM(oi.Qty) as TotalItemsSold
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
WHERE o.Date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
  AND o.Status >= 1  -- Confirmed orders and above
GROUP BY YEAR(o.Date), MONTH(o.Date)
ORDER BY Year DESC, Month DESC;
```

### Variations
- **Daily**: GROUP BY DATE(o.Date)
- **Weekly**: GROUP BY YEARWEEK(o.Date)
- **Quarterly**: GROUP BY YEAR(o.Date), QUARTER(o.Date)

---

## Pattern 2: Top Performers Reports

### Purpose
Identify top customers, products, or salespeople by various metrics.

### Example: Top 10 Customers by Revenue
```sql
SELECT 
    c.Customer,
    c.Name as CustomerName,
    c.City,
    c.State,
    COUNT(o.Wo) as OrderCount,
    SUM(o.Total) as TotalRevenue,
    AVG(o.Total) as AverageOrderValue,
    MAX(o.Date) as LastOrderDate,
    DATEDIFF(CURDATE(), MAX(o.Date)) as DaysSinceLastOrder
FROM db_customer c
JOIN db_order o ON c.Customer = o.Customer
WHERE o.Date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
  AND o.Status >= 1
GROUP BY c.Customer, c.Name, c.City, c.State
HAVING SUM(o.Total) > 0
ORDER BY TotalRevenue DESC
LIMIT 10;
```

### Variations
- **Top Products**: Group by Product
- **Top Salespeople**: Group by Salesperson
- **Top Categories**: Group by Product Category

---

## Pattern 3: Trend Analysis

### Purpose
Compare current performance to previous periods to identify trends.

### Example: Year-over-Year Sales Comparison
```sql
SELECT 
    current_year.Month,
    current_year.MonthName,
    current_year.Revenue as CurrentYearRevenue,
    previous_year.Revenue as PreviousYearRevenue,
    ROUND(
        ((current_year.Revenue - previous_year.Revenue) / previous_year.Revenue) * 100, 
        2
    ) as PercentChange,
    current_year.OrderCount as CurrentYearOrders,
    previous_year.OrderCount as PreviousYearOrders
FROM (
    -- Current year data
    SELECT 
        MONTH(Date) as Month,
        MONTHNAME(Date) as MonthName,
        SUM(Total) as Revenue,
        COUNT(*) as OrderCount
    FROM db_order
    WHERE YEAR(Date) = YEAR(CURDATE())
      AND Status >= 1
    GROUP BY MONTH(Date), MONTHNAME(Date)
) current_year
LEFT JOIN (
    -- Previous year data
    SELECT 
        MONTH(Date) as Month,
        SUM(Total) as Revenue,
        COUNT(*) as OrderCount
    FROM db_order
    WHERE YEAR(Date) = YEAR(CURDATE()) - 1
      AND Status >= 1
    GROUP BY MONTH(Date)
) previous_year ON current_year.Month = previous_year.Month
ORDER BY current_year.Month;
```

---

## Pattern 4: Inventory Status Reports

### Purpose
Generate reports on inventory levels, stock movement, and reorder needs.

### Example: Inventory Status Summary
```sql
SELECT 
    p.Product,
    p.Description,
    p.Category,
    COALESCE(current_stock.OnHand, 0) as OnHandQty,
    COALESCE(reserved_stock.Reserved, 0) as ReservedQty,
    COALESCE(current_stock.OnHand, 0) - COALESCE(reserved_stock.Reserved, 0) as AvailableQty,
    p.ReorderPoint,
    p.ReorderQty,
    CASE 
        WHEN COALESCE(current_stock.OnHand, 0) - COALESCE(reserved_stock.Reserved, 0) <= p.ReorderPoint 
        THEN 'Reorder Needed'
        WHEN COALESCE(current_stock.OnHand, 0) - COALESCE(reserved_stock.Reserved, 0) <= p.ReorderPoint * 1.5 
        THEN 'Low Stock'
        ELSE 'Adequate'
    END as StockStatus
FROM db_product p
LEFT JOIN (
    SELECT 
        Product,
        SUM(Qty) as OnHand
    FROM db_stock
    WHERE Status = 'Available'
    GROUP BY Product
) current_stock ON p.Product = current_stock.Product
LEFT JOIN (
    SELECT 
        oi.Product,
        SUM(oi.Qty) as Reserved
    FROM db_orderitem oi
    JOIN db_order o ON oi.Wo = o.Wo
    WHERE o.Status IN (1, 2)  -- Active and processing orders
    GROUP BY oi.Product
) reserved_stock ON p.Product = reserved_stock.Product
WHERE p.Status = 'Active'
ORDER BY StockStatus DESC, p.Category, p.Product;
```

---

## Pattern 5: Customer Activity Reports

### Purpose
Analyze customer behavior, ordering patterns, and engagement.

### Example: Customer Activity Analysis
```sql
SELECT 
    c.Customer,
    c.Name as CustomerName,
    c.Type as CustomerType,
    COUNT(o.Wo) as TotalOrders,
    SUM(o.Total) as TotalRevenue,
    AVG(o.Total) as AverageOrderValue,
    MIN(o.Date) as FirstOrderDate,
    MAX(o.Date) as LastOrderDate,
    DATEDIFF(MAX(o.Date), MIN(o.Date)) as CustomerLifespanDays,
    CASE 
        WHEN MAX(o.Date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) THEN 'Active'
        WHEN MAX(o.Date) >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) THEN 'Recent'
        WHEN MAX(o.Date) >= DATE_SUB(CURDATE(), INTERVAL 365 DAY) THEN 'Dormant'
        ELSE 'Inactive'
    END as ActivityStatus,
    COUNT(DISTINCT oi.Product) as UniqueProductsPurchased
FROM db_customer c
LEFT JOIN db_order o ON c.Customer = o.Customer AND o.Status >= 1
LEFT JOIN db_orderitem oi ON o.Wo = oi.Wo
WHERE c.Status = 'Active'
GROUP BY c.Customer, c.Name, c.Type
ORDER BY TotalRevenue DESC;
```

---

## Pattern 6: Product Performance Reports

### Purpose
Analyze product sales performance, profitability, and trends.

### Example: Product Performance Analysis
```sql
SELECT 
    p.Product,
    p.Description,
    p.Category,
    COUNT(DISTINCT oi.Wo) as OrdersContaining,
    SUM(oi.Qty) as TotalQuantitySold,
    SUM(oi.SubTotal) as TotalRevenue,
    AVG(oi.SubTotal / oi.Qty) as AverageUnitPrice,
    COUNT(DISTINCT o.Customer) as UniqueCustomers,
    MIN(o.Date) as FirstSaleDate,
    MAX(o.Date) as LastSaleDate,
    ROUND(
        SUM(oi.SubTotal) / SUM(SUM(oi.SubTotal)) OVER() * 100,
        2
    ) as RevenuePercentage
FROM db_product p
JOIN db_orderitem oi ON p.Product = oi.Product
JOIN db_order o ON oi.Wo = o.Wo
WHERE o.Date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
  AND o.Status >= 1
  AND p.Status = 'Active'
GROUP BY p.Product, p.Description, p.Category
HAVING SUM(oi.Qty) > 0
ORDER BY TotalRevenue DESC;
```

---

## Report Customization Tips

### Date Range Parameters
Replace fixed dates with parameters:
```sql
WHERE o.Date BETWEEN @StartDate AND @EndDate
```

### Status Filtering
Always filter by appropriate status:
```sql
WHERE o.Status >= 1  -- Confirmed orders and above
```

### Performance Considerations
1. **Use indexes** on date and status columns
2. **Limit date ranges** for large datasets
3. **Consider pagination** for large result sets
4. **Cache results** for frequently run reports

### Export-Friendly Formatting
```sql
SELECT 
    DATE_FORMAT(Date, '%Y-%m-%d') as OrderDate,
    FORMAT(Total, 2) as FormattedTotal
```

## Common Report Scheduling Patterns

### Daily Reports
- Previous day sales
- Inventory alerts
- Order status updates

### Weekly Reports  
- Week-over-week comparisons
- Sales team performance
- Top customer activity

### Monthly Reports
- Financial summaries
- Product performance
- Customer analysis
- Trend reports

### Quarterly Reports
- Business reviews
- Strategic analysis
- Year-over-year comparisons