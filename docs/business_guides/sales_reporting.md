# Sales Reporting Queries

## Overview
Sales reporting provides insights into revenue performance, sales trends, and team productivity. These queries support management reporting and sales analysis.

## Common Data Needs
- Revenue tracking and analysis
- Sales team performance
- Product sales analysis
- Customer sales patterns
- Time-based sales trends

## Key Tables
- **db_order**: Sales orders
- **db_orderitem**: Order line items  
- **db_salesperson**: Sales team data
- **db_customer**: Customer information
- **db_product**: Product catalog

---

## Example 1: Sales Performance Report

### Business Purpose
Generate comprehensive sales reports for management review and analysis.

### SQL Query
```sql
SELECT oi.ItemBatch AS Batch,
       e.Box AS NumeroDeCaja,
       o.Wo AS Orden,
       oi.item,
       pr.Description AS Product,
       f.Qty,
       oi.SubTotal AS "Unit Price",
       Sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor))/oi.Qty)) AS "Unit Cost",
       oi.SubTotal*f.Qty AS "Line Price",
       sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor))/oi.Qty)*f.Qty) AS "Line Cost"
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_orderiteminv oiv ON oi.Wo = oiv.Wo
AND oi.Item = oiv.Item
JOIN db_stock stc ON oiv.Stock = stc.Stock
JOIN db_stockbalance stcb ON stc.Stock = stcb.Stock
AND stcb.Warehouse='[value]'
JOIN db_stockbalancecomp stcbc ON stcb.Balno = stcbc.Balno
JOIN db_product pr ON oi.Product = pr.Product
JOIN db_customer cus ON o.Customer=cus.Customer
JOIN db_mfgitem b ON oi.Product = b.Product
JOIN db_mfg c ON b.Category = c.Category
JOIN db_status st ON (o.Status=st.Status
                      AND st.Type='[value]')
JOIN db_bom bom ON (oi.Product=bom.Product
                    AND oi.Model=bom.Model)
JOIN db_color color ON (oi.Color=color.Color
                        AND bom.ColorTable=color.ColorTable)
JOIN db_box e ON oi.Wo=e.Wo
JOIN db_boxitem f ON e.Box=f.Box
AND oi.Item=f.I
WHERE (oiv.Required>'[value]')
  AND (o.Wo='[value]')
GROUP BY e.Box,
         oi.Wo,
         oi.Item
ORDER BY e.Box,
         oi.Wo ASC,
         oi.Item ASC
```

### Key Concepts
- Revenue calculation and tracking
- Performance measurement
- Trend analysis

---

## Example 2: Sales Performance Report

### Business Purpose
Generate comprehensive sales reports for management review and analysis.

### SQL Query
```sql
SELECT oi.ItemBatch AS Batch,
       o.Wo AS Orden,
       oi.item,
       pr.Description AS Product,
       oi.Qty,
       oi.SubTotal AS "Unit Price",
       Sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor))/oi.Qty)) AS "Unit Cost",
       oi.SubTotal*oi.Qty AS "Line Price",
       sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor)))) AS "Line Cost"
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_orderiteminv oiv ON oi.Wo = oiv.Wo
AND oi.Item = oiv.Item
JOIN db_stock stc ON oiv.Stock = stc.Stock
JOIN db_stockbalance stcb ON stc.Stock = stcb.Stock
AND stcb.Warehouse='[value]'
JOIN db_stockbalancecomp stcbc ON stcb.Balno = stcbc.Balno
JOIN db_product pr ON oi.Product = pr.Product
JOIN db_customer cus ON o.Customer=cus.Customer
JOIN db_mfgitem b ON oi.Product = b.Product
JOIN db_mfg c ON b.Category = c.Category
JOIN db_status st ON (o.Status=st.Status
                      AND st.Type='[value]')
JOIN db_bom bom ON (oi.Product=bom.Product
                    AND oi.Model=bom.Model)
JOIN db_color color ON (oi.Color=color.Color
                        AND bom.ColorTable=color.ColorTable)
WHERE (oiv.Required>'[value]')
  AND (o.Wo='[value]')
GROUP BY oi.Wo,
         oi.Item
ORDER BY oi.Wo ASC,
         oi.Item ASC
```

### Key Concepts
- Revenue calculation and tracking
- Performance measurement
- Trend analysis

---

## Example 3: Sales Performance Report

### Business Purpose
Generate comprehensive sales reports for management review and analysis.

### SQL Query
```sql
SELECT oi.ItemBatch AS Batch,
       o.Wo AS Orden,
       oi.item,
       pr.Description AS Product,
       oi.Qty,
       oi.SubTotal AS "Unit Price",
       Sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor))/oi.Qty)) AS "Unit Cost",
       oi.SubTotal*oi.Qty AS "Line Price",
       sum(((stc.StandardCost*(oiv.Required/stc.ReliefFactor)))) AS "Line Cost"
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_orderiteminv oiv ON oi.Wo = oiv.Wo
AND oi.Item = oiv.Item
JOIN db_stock stc ON oiv.Stock = stc.Stock
JOIN db_stockbalance stcb ON stc.Stock = stcb.Stock
AND stcb.Warehouse='[value]'
JOIN db_stockbalancecomp stcbc ON stcb.Balno = stcbc.Balno
JOIN db_product pr ON oi.Product = pr.Product
JOIN db_customer cus ON o.Customer=cus.Customer
JOIN db_mfgitem b ON oi.Product = b.Product
JOIN db_mfg c ON b.Category = c.Category
JOIN db_status st ON (o.Status=st.Status
                      AND st.Type='[value]')
JOIN db_bom bom ON (oi.Product=bom.Product
                    AND oi.Model=bom.Model)
JOIN db_color color ON (oi.Color=color.Color
                        AND bom.ColorTable=color.ColorTable)
WHERE (oiv.Required>'[value]')
  AND oi.Wo IN('[value]')
GROUP BY oi.Wo,
         oi.Item
ORDER BY oi.Wo ASC,
         oi.Item ASC
```

### Key Concepts
- Revenue calculation and tracking
- Performance measurement
- Trend analysis

---

