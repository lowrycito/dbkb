# Financial Analysis Queries

## Overview
Financial analysis queries support accounting, cost analysis, and financial reporting needs. These help track profitability and financial performance.

## Common Data Needs
- Cost analysis and profitability
- Financial reporting
- Budget vs actual analysis
- Cash flow tracking
- Vendor payment analysis

## Key Tables
- **db_ap**: Accounts payable
- **db_check**: Check payments
- **db_vendor**: Vendor information
- **db_gl**: General ledger

---

## Example 1: Financial Analysis

### Business Purpose
Analyze financial performance and cost structures.

### SQL Query
```sql
SELECT a.Salesperson,
       CONCAT(e.FirstName, " ", e.Name) AS Name,
       c.CapacityGroup,
       d.Description AS ProductGroup,
       b.Product,
       c.Description AS ProductDescription,
       SUM(b.SubTotal * b.Quantity) AS SalesTotal
FROM db_invoice a
INNER JOIN db_invoiceitem b ON a.Invoice=b.Invoice
INNER JOIN db_product c ON b.Product=c.Product
LEFT JOIN db_productgroup d ON c.CapacityGroup=d.GGroup
LEFT JOIN db_salesperson e ON a.Salesperson=e.Salesperson
WHERE a.Date BETWEEN '[value]' AND '[value]'
  AND a.Salesperson BETWEEN '[value]' AND '[value]'
  AND a.Invoice >'[value]'
  AND a.Status <> '[value]'
  AND (a.Total >'[value]'
       OR b.Product BETWEEN '[value]' AND '[value]')
  AND c.CapacityGroup BETWEEN '[value]' AND '[value]'
GROUP BY a.Salesperson,
         c.CapacityGroup,
         b.Product
ORDER BY a.Salesperson,
         c.CapacityGroup,
         b.Product
```

### Key Concepts
- Cost calculation and analysis
- Financial performance tracking
- Profitability measurement

---

## Example 2: Financial Analysis

### Business Purpose
Analyze financial performance and cost structures.

### SQL Query
```sql
SELECT a.Site,
       c.CapacityGroup,
       j.Description AS GroupDescription,
       b.Product,
       c.Description AS ProductDescription,
       COUNT(DISTINCT a.Invoice) AS InvoiceCount,
       SUM(b.SubTotal * b.Quantity) AS SalesTotal
FROM db_invoice a
INNER JOIN db_invoiceitem b ON a.Invoice=b.Invoice
INNER JOIN db_product c ON b.Product=c.Product
LEFT JOIN db_productgroup j ON c.CapacityGroup=j.GGroup
WHERE a.Date BETWEEN '[value]' AND '[value]'
  AND a.Invoice >'[value]'
  AND a.Status <> '[value]'
  AND a.Total >'[value]'
  AND c.CapacityGroup BETWEEN '[value]' AND '[value]'
  AND a.Site='[value]'
GROUP BY c.CapacityGroup,
         GroupDescription,
         b.Product,
         ProductDescription
ORDER BY c.CapacityGroup,
         GroupDescription,
         b.Product,
         ProductDescription
```

### Key Concepts
- Cost calculation and analysis
- Financial performance tracking
- Profitability measurement

---

## Example 3: Financial Analysis

### Business Purpose
Analyze financial performance and cost structures.

### SQL Query
```sql
SELECT i.Invoice,
       i.Status,
       i.Date,
       i.GlPeriod,
       i.Customer AS '[value]', i.Total,
                                d.Salesperson AS '[value]'
FROM db_invoice i
JOIN db_customersalesperson d ON i.Customer=d.Customer
AND d.I='[value]'
JOIN db_invoiceitem ii ON i.Invoice=ii.Invoice
JOIN db_product p ON ii.Product=p.Product
WHERE i.GlPeriod BETWEEN '[value]' AND '[value]'
GROUP BY i.Invoice
```

### Key Concepts
- Cost calculation and analysis
- Financial performance tracking
- Profitability measurement

---

