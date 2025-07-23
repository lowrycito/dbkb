# Advanced Query Patterns: Complex Joins

## Overview
Complex joins allow you to combine data from multiple tables to create comprehensive reports and analysis. These patterns are essential for advanced ERP reporting.

## Pattern 1: Multi-Table Joins

### Purpose
Combine data from multiple related tables to get complete information.

### Example: Complete Order Information
```sql
SELECT 
    o.Wo as OrderNumber,
    c.Name as CustomerName,
    c.Phone as CustomerPhone,
    oi.Item,
    p.Description as ProductDescription,
    oi.Qty as Quantity,
    oi.SubTotal as LineTotal,
    o.Total as OrderTotal,
    s.Description as OrderStatus
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_product p ON oi.Product = p.Product
JOIN db_status s ON o.Status = s.Status AND s.Type = 'ORDER'
WHERE o.Date >= '2025-01-01'
ORDER BY o.Date DESC, oi.Item;
```

### Key Concepts
- **Multiple JOINs**: Chain tables together
- **Composite keys**: Match on multiple conditions
- **Logical grouping**: Keep related joins together

---

## Pattern 2: LEFT JOINs for Optional Data

### Purpose
Include all records from the main table, even if related data doesn't exist.

### Example: Orders with Optional Shipping Information
```sql
SELECT 
    o.Wo,
    c.Name as CustomerName,
    o.Total,
    COALESCE(sh.TrackingNumber, 'Not Shipped') as Tracking,
    COALESCE(sh.ShipDate, 'Pending') as ShipDate
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
LEFT JOIN db_shipping sh ON o.Wo = sh.Wo
WHERE o.Date >= '2025-01-01'
ORDER BY o.Date DESC;
```

### Key Concepts
- **LEFT JOIN**: Keep all left table records
- **COALESCE()**: Handle NULL values
- **Optional relationships**: Not all orders have shipping

---

## Pattern 3: Subqueries in Joins

### Purpose
Use calculated values from subqueries in your joins.

### Example: Orders with Item Counts
```sql
SELECT 
    o.Wo,
    c.Name as CustomerName,
    o.Total,
    item_counts.ItemCount,
    item_counts.TotalQty
FROM db_order o
JOIN db_customer c ON o.Customer = c.Customer
JOIN (
    SELECT 
        Wo,
        COUNT(*) as ItemCount,
        SUM(Qty) as TotalQty
    FROM db_orderitem
    GROUP BY Wo
) item_counts ON o.Wo = item_counts.Wo
WHERE o.Date >= '2025-01-01'
ORDER BY item_counts.ItemCount DESC;
```

### Key Concepts
- **Subquery JOINs**: Pre-calculate aggregations
- **Derived tables**: Treat subqueries as tables
- **Performance**: Can be faster than multiple queries

---

## Pattern 4: Self-Joins

### Purpose
Join a table to itself to find relationships within the same table.

### Example: Find Related Products
```sql
SELECT 
    p1.Product as MainProduct,
    p1.Description as MainDescription,
    p2.Product as RelatedProduct,
    p2.Description as RelatedDescription
FROM db_product p1
JOIN db_product p2 ON p1.Category = p2.Category 
                   AND p1.Product != p2.Product
WHERE p1.Product = 'PROD001'
ORDER BY p2.Description;
```

### Key Concepts
- **Self-JOIN**: Table joined to itself
- **Aliases required**: p1 and p2 distinguish instances
- **Exclusion logic**: Avoid matching record to itself

---

## Pattern 5: Complex Filtering with Joins

### Purpose
Use joined tables for complex filtering conditions.

### Example: Customers with Large Orders
```sql
SELECT DISTINCT
    c.Customer,
    c.Name,
    c.Email,
    large_orders.MaxOrderValue
FROM db_customer c
JOIN (
    SELECT 
        Customer,
        MAX(Total) as MaxOrderValue
    FROM db_order
    WHERE Date >= '2025-01-01'
    GROUP BY Customer
    HAVING MAX(Total) > 10000
) large_orders ON c.Customer = large_orders.Customer
ORDER BY large_orders.MaxOrderValue DESC;
```

### Key Concepts
- **DISTINCT**: Remove duplicates
- **HAVING**: Filter after grouping
- **Complex criteria**: Use subqueries for advanced filtering

---

## Pattern 6: Inventory and Order Integration

### Purpose
Complex joins between order and inventory systems.

### Example: Order Items with Inventory Status
```sql
SELECT 
    o.Wo,
    oi.Item,
    p.Description,
    oi.Qty as OrderedQty,
    COALESCE(inv.AvailableQty, 0) as AvailableQty,
    CASE 
        WHEN COALESCE(inv.AvailableQty, 0) >= oi.Qty THEN 'In Stock'
        WHEN COALESCE(inv.AvailableQty, 0) > 0 THEN 'Partial Stock'
        ELSE 'Out of Stock'
    END as StockStatus
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_product p ON oi.Product = p.Product
LEFT JOIN (
    SELECT 
        Product,
        SUM(Qty) as AvailableQty
    FROM db_stock
    WHERE Status = 'Available'
    GROUP BY Product
) inv ON p.Product = inv.Product
WHERE o.Status = 1  -- Active orders
ORDER BY o.Wo, oi.Item;
```

### Key Concepts
- **CASE statements**: Conditional logic
- **Inventory aggregation**: Sum across warehouses
- **Stock status logic**: Business rule implementation

---

## Performance Tips for Complex Joins

1. **Index your join columns**
   - Ensure foreign keys are indexed
   - Consider composite indexes for multi-column joins

2. **Filter early**
   ```sql
   WHERE o.Date >= '2025-01-01'  -- Apply before joins when possible
   ```

3. **Use appropriate join types**
   - INNER JOIN: Only matching records
   - LEFT JOIN: All left records + matches
   - Avoid FULL OUTER JOIN unless necessary

4. **Limit subquery complexity**
   - Break complex queries into steps
   - Consider temporary tables for very complex logic

5. **Test with EXPLAIN**
   ```sql
   EXPLAIN SELECT ... -- Check query execution plan
   ```

## Common Anti-Patterns to Avoid

- **Cartesian products**: Always specify join conditions
- **Too many LEFT JOINs**: Can create performance issues
- **Nested subqueries**: Consider CTEs for readability
- **Missing indexes**: Ensure join columns are indexed