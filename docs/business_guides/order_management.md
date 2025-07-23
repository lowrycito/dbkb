# Order Management Queries

## Overview
Order management is the core of the ERP system, tracking orders from creation to fulfillment. These queries help you analyze order performance, track order status, and understand order profitability.

## Common Data Needs
- Order status and tracking
- Order profitability analysis  
- Customer order history
- Order item details and inventory requirements
- Order fulfillment tracking

## Key Tables
- **db_order**: Main order information
- **db_orderitem**: Individual items within orders
- **db_orderiteminv**: Inventory requirements for order items
- **db_customer**: Customer information
- **db_product**: Product catalog

---

## Example 1: Order Cost Analysis

### Business Purpose
Analyze the cost structure of orders including unit costs, line costs, and profitability. This helps understand margins and identify high-value orders.

### When to Use
- Monthly profitability reviews
- Order pricing analysis
- Cost accounting reports
- Management dashboards

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
- **StandardCost**: Base cost of materials used
- **ReliefFactor**: Manufacturing efficiency factor
- **ItemBatch**: Groups related order items
- **SubTotal**: Unit price before taxes

### Sample Use Cases
- Calculate profit margins by order
- Identify most/least profitable products
- Track cost trends over time
- Analyze warehouse efficiency

---

## Example 2: Order Cost Analysis

### Business Purpose
Analyze the cost structure of orders including unit costs, line costs, and profitability. This helps understand margins and identify high-value orders.

### When to Use
- Monthly profitability reviews
- Order pricing analysis
- Cost accounting reports
- Management dashboards

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
- **StandardCost**: Base cost of materials used
- **ReliefFactor**: Manufacturing efficiency factor
- **ItemBatch**: Groups related order items
- **SubTotal**: Unit price before taxes

### Sample Use Cases
- Calculate profit margins by order
- Identify most/least profitable products
- Track cost trends over time
- Analyze warehouse efficiency

---

## Example 3: Order Cost Analysis

### Business Purpose
Analyze the cost structure of orders including unit costs, line costs, and profitability. This helps understand margins and identify high-value orders.

### When to Use
- Monthly profitability reviews
- Order pricing analysis
- Cost accounting reports
- Management dashboards

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
- **StandardCost**: Base cost of materials used
- **ReliefFactor**: Manufacturing efficiency factor
- **ItemBatch**: Groups related order items
- **SubTotal**: Unit price before taxes

### Sample Use Cases
- Calculate profit margins by order
- Identify most/least profitable products
- Track cost trends over time
- Analyze warehouse efficiency

---

## Example 4: Order Cost Analysis

### Business Purpose
Analyze the cost structure of orders including unit costs, line costs, and profitability. This helps understand margins and identify high-value orders.

### When to Use
- Monthly profitability reviews
- Order pricing analysis
- Cost accounting reports
- Management dashboards

### SQL Query
```sql
SELECT concat(date_format(IF(?='[value]'
                             OR '[value]' = '[value]', '[value]', '[value]'), '[value]'), '[value]', IF(?='[value]'
                                                                                                                                     OR '[value]' = '[value]', '[value]', '[value]'), '[value]', date_format(IF(?='[value]'
                                                                                                                                                                                                                                OR '[value]' = '[value]', '[value]', '[value]'), '[value]'), '[value]', IF(?='[value]'
                                                                                                                                                                                                                                                                                                                                      OR '[value]' = '[value]', '[value]', '[value]'))AS Busqueda,
       g.ShipDate,
       cus.Name,
       concat(o.Wo, '[value]', oi.Item)AS escaneo,
       o.Wo,
       oi.Item,
       oi.Qty,
       CAST(get_prompt_code(oi.PromptAnswers, '[value]', '[value]') AS DECIMAL('[value]', '[value]')) AS WD,
       CAST(get_prompt_code(oi.PromptAnswers, '[value]', '[value]') AS DECIMAL('[value]', '[value]')) AS LN,
       (IF(oi.Product IN ("?", "?", "?") ,"Si", "")) AS NoTools,
       oiv.Stock,
       stk.Description
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
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
JOIN db_orderiteminv oiv ON (oi.Wo = oiv.Wo
                             AND oi.Item = oiv.Item)
JOIN db_stock stk ON oiv.Stock=stk.Stock
JOIN db_box e ON oi.Wo=e.Wo
JOIN db_boxitem f ON e.Box=f.Box
AND oi.Item=f.I
JOIN db_boxship g ON e.Box=g.Box
WHERE g.TimeCreated BETWEEN date_add(TIMESTAMP(IF(?='[value]'
                                                  OR '[value]' = '[value]', '[value]', '[value]'), IF(?='[value]'
                                                                                                                                        OR '[value]' = '[value]', '[value]', '[value]')) ,interval '[value]' HOUR) AND date_add(TIMESTAMP(IF(?='[value]'
                                                                                                                                                                                                                                                         OR '[value]' = '[value]', '[value]', '[value]'), IF(?='[value]'
                                                                                                                                                                                                                                                                                                                                             OR '[value]' = '[value]', '[value]', '[value]')) ,interval '[value]' HOUR)
  AND oiv.Required>'[value]'
  AND if(?="", TRUE, o.Customer='[value]')
  AND mid(oiv.Stock, '[value]', '[value]')="?"
ORDER BY o.Wo DESC,
         oi.Item ASC
```

### Key Concepts
- **StandardCost**: Base cost of materials used
- **ReliefFactor**: Manufacturing efficiency factor
- **ItemBatch**: Groups related order items
- **SubTotal**: Unit price before taxes

### Sample Use Cases
- Calculate profit margins by order
- Identify most/least profitable products
- Track cost trends over time
- Analyze warehouse efficiency

---

## Example 5: Order Cost Analysis

### Business Purpose
Analyze the cost structure of orders including unit costs, line costs, and profitability. This helps understand margins and identify high-value orders.

### When to Use
- Monthly profitability reviews
- Order pricing analysis
- Cost accounting reports
- Management dashboards

### SQL Query
```sql
SELECT oi.ItemBatch AS Batch,
       o.Date AS OrderDate,
       o.Status,
       o.Wo AS Orden,
       oi.item,
       oi.Qty,
       get_prompt_code(oi.PromptAnswers, '[value]', '[value]') AS Width,
       get_prompt_code(oi.PromptAnswers, '[value]', '[value]') AS LENGTH,
       oiv.Stock,
       stc.PurchaseUnit AS PurchaseUnit,
       oiv.Required,
       oiv.Warehouse,
       stc.ReliefUnit AS ReliefUnit,
       stc.ReliefFactor AS ReliefFactor,
       b.Product,
       pr.Description,
       c.Description AS Categoria,
       ordn.Date,
       ordn.Comment
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
JOIN db_orderiteminv oiv ON oi.Wo = oiv.Wo
AND oi.Item = oiv.Item
JOIN db_stock stc ON oiv.Stock = stc.Stock
JOIN db_ordernotes ordn ON o.Wo = ordn.Wo
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
  AND (b.Category BETWEEN '[value]' AND '[value]')
  AND ((oi.Qty-oi.QtyShipped-oi.QtyCancelled)>'[value]')
  AND (oiv.Stock='[value]')
  AND (o.Status IN (?,
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]',
                    '[value]'))
  AND if(?="", TRUE, oi.ItemBatch='[value]')
  AND ordn.Date>= "?-?-?"
  AND ordn.Comment like "%UN-BATCHED%"
ORDER BY oi.ItemBatch,
         o.Wo DESC,
         oi.Item ASC
```

### Key Concepts
- **StandardCost**: Base cost of materials used
- **ReliefFactor**: Manufacturing efficiency factor
- **ItemBatch**: Groups related order items
- **SubTotal**: Unit price before taxes

### Sample Use Cases
- Calculate profit margins by order
- Identify most/least profitable products
- Track cost trends over time
- Analyze warehouse efficiency

---

