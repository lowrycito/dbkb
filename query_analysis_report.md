# Query Pattern Analysis Report
Generated: 2025-05-23 19:36:29

## Dataset Overview
- total_files: 9121
- processed_files: 9121
- files_with_queries: 9119
- unique_queries: 6086
- duplicate_queries_removed: 3033
- extraction_date: 2025-05-23

## Most Frequently Used Tables
| Rank | Table Name | Usage Count | Percentage |
|------|------------|-------------|------------|
| 1 | db_order | 3478 | 57.1% |
| 2 | db_orderitem | 2929 | 48.1% |
| 3 | db_customer | 2367 | 38.9% |
| 4 | db_product | 1927 | 31.7% |
| 5 | db_stock | 772 | 12.7% |
| 6 | db_status | 770 | 12.7% |
| 7 | db_salesperson | 666 | 10.9% |
| 8 | db_invoice | 625 | 10.3% |
| 9 | db_color | 563 | 9.3% |
| 10 | db_bom | 509 | 8.4% |
| 11 | db_mfgitem | 466 | 7.7% |
| 12 | db_orderiteminv | 429 | 7.0% |
| 13 | db_invoiceitem | 417 | 6.9% |
| 14 | db_ordersalesperson | 414 | 6.8% |
| 15 | db_mfg | 379 | 6.2% |
| 16 | db_productgroup | 362 | 5.9% |
| 17 | db_box | 361 | 5.9% |
| 18 | db_orderitemprod | 358 | 5.9% |
| 19 | db_po | 355 | 5.8% |
| 20 | db_customersalesperson | 343 | 5.6% |

## Common Join Patterns
| Main Table | Commonly Joined With | Join Count |
|------------|----------------------|------------|
| AS | db_cid, db_stock, db_stockbalance | 3 |
| FROM | db_stock, db_warehouse | 2 |
| GROUP_CONCAT | db_customer, db_order, db_orderitemprod, db_orderitemvar, db_ordertype (+4 more) | 9 |
| IFNULL | db_customer, db_order, db_orderitemprod, db_orderitemvar, db_ordertype (+4 more) | 9 |
| JRL_productstandardvalidation | db_product, db_productprompt, db_productpromptvalue | 3 |
| Warehouse | db_ponotes | 1 |
| change_gl | db_hgl | 1 |
| db_accounttype | db_customersalesperson | 1 |
| db_achclient | db_customer | 1 |
| db_activity | db_loginid | 1 |
| db_advance | db_cash, db_creditmemo | 2 |
| db_ap | db_apitem, db_apitemgl, db_bank, db_check, db_checkitem (+25 more) | 30 |
| db_apilog | db_apilogdetail, db_apilogkeyvalue, db_product, db_warehouse | 4 |
| db_apitem | db_ap, db_apitemgl, db_checkitem, db_gl, db_po (+4 more) | 9 |
| db_bom | db_bomcomponent, db_color, db_coordination, db_coordinationdetail, db_laborstd (+4 more) | 9 |
| db_bomcomponent | db_bom, db_color, db_mfgitem, db_model, db_order (+8 more) | 13 |
| db_box | db_bom, db_boxitem, db_boxship, db_color, db_customer (+11 more) | 16 |
| db_boxitem | db_box, db_boxship, db_customer, db_invoice, db_order (+7 more) | 12 |
| db_boxship | db_box, db_boxitem, db_carrier, db_customer, db_customersalesperson (+15 more) | 20 |
| db_cash | db_achclient, db_authorizenet_capture, db_bank, db_cashadvanceapplied, db_cashitem (+15 more) | 20 |
| db_cashitem | db_invoice | 1 |
| db_chartofaccounts | db_gl, db_hgl | 2 |
| db_check | db_ap, db_checkitem, db_status, db_vendor | 4 |
| db_cid | db_stock, db_stockclass, db_vendorstock, db_warehouse, db_warehouselocation | 5 |
| db_client | db_customer, db_order, db_orderitem | 3 |
| db_color | db_bom, db_colorconstant, db_order, db_orderitem, db_orderiteminv (+4 more) | 9 |
| db_coordination | db_coordinationdetail | 1 |
| db_coordinationdetail | db_bom, db_bomcomponent, db_stock | 3 |
| db_creditmemo | db_customer, db_customersalesperson | 2 |
| db_crmappointment | db_crmappointmentloginid, db_crmappointmentrelationship, db_crmappointmenttype, db_loginid, db_order | 5 |
| db_crmcategory | db_crmcategorystatus, db_crmstatus | 2 |
| db_crmtask | db_crmcategory, db_crmstatus, db_crmtaskaction, db_customer, db_customersalesperson (+9 more) | 14 |
| db_crmtasktrigger | db_crmcategory, db_crmstatus, db_loginid, db_team | 4 |
| db_customer | db_accounttype, db_box, db_boxitem, db_boxship, db_cashpaymentprofile (+37 more) | 42 |
| db_customerar | db_customer | 1 |
| db_customergroupitem | db_customer, db_customergroup | 2 |
| db_customerhistory | db_customer | 1 |
| db_customernotes | db_customer | 1 |
| db_customerproject | db_customer, db_customerprojectstatus, db_customerprojecttype, db_loginid, db_order (+1 more) | 6 |
| db_customersalesperson | db_customer, db_invoice, db_order, db_salesperson | 4 |
| db_customfield | db_customer, db_customfieldvalue | 2 |
| db_customfieldvalue | db_customfield, db_event, db_eventtype, db_order, db_orderitem (+1 more) | 6 |
| db_cycle | db_cycle_location, db_cycle_location_cid, db_warehouse | 3 |
| db_cycle_location | db_cycle | 1 |
| db_cycle_location_cid | db_cid, db_cycle, db_stock | 3 |
| db_departmentqueue | db_department, db_order, db_orderitem, db_product | 4 |
| db_discount | db_discountcat | 1 |
| db_ediasn | db_ediasnitem | 1 |
| db_editoxmltranslateitem | db_color | 1 |
| db_employee | db_employeedepartment | 1 |
| db_event | db_customer, db_customersalesperson, db_customfield, db_customfieldvalue, db_eventappointment (+16 more) | 21 |
| db_eventappointment | db_customer, db_customersalesperson, db_event, db_eventtype, db_order (+3 more) | 8 |
| db_hdxmlinvoice | db_ap, db_hdxmlinvoiceitem, db_po, db_poitem, db_status | 5 |
| db_hjournal | db_gl, db_hjournalitem, db_hjournalitemdetail, db_loginid, db_stockbalancecomp (+1 more) | 6 |
| db_hjournalitemdetail | db_cash, db_creditmemo, db_hjournal, db_loginid | 4 |
| db_import | db_importcolumn | 1 |
| db_invoice | db_accounttype, db_ap, db_apitem, db_bank, db_bom (+48 more) | 53 |
| db_invoiceitem | db_accounttype, db_bom, db_color, db_customer, db_customersalesperson (+13 more) | 18 |
| db_invoicetranx | db_invoice | 1 |
| db_journal | db_customer, db_eventtype, db_gl, db_hgl, db_hjournalitem (+14 more) | 19 |
| db_journalitem | db_gl, db_journal | 2 |
| db_journalitemdetail | db_cash, db_creditmemo, db_gl, db_journal, db_loginid | 5 |
| db_lead | db_crmstatus, db_crmtask, db_loginid, db_marketingsource, db_ordernotes (+2 more) | 7 |
| db_log | db_loginid | 1 |
| db_loginid | db_box, db_boxitem, db_boxship, db_crmtask, db_crmtaskaction (+17 more) | 22 |
| db_mfg | db_box, db_boxitem, db_boxship, db_customer, db_mfgitem (+4 more) | 9 |
| db_mfgitem | db_mfg, db_product, db_productprompt, db_productpromptvalue | 4 |
| db_mts | db_bomcomponent, db_orderitem, db_orderiteminv, db_stock, db_stockbalance (+1 more) | 6 |
| db_order | db_accounttype, db_ap, db_apitem, db_bom, db_bomcomponent (+112 more) | 117 |
| db_ordercopy | db_customer, db_loginid, db_order, db_status | 4 |
| db_orderdeposit | db_order, db_site | 2 |
| db_orderhistory | db_customer, db_customerhistory, db_loginid, db_order, db_orderitem (+4 more) | 9 |
| db_orderitem | db_accounttype, db_bom, db_box, db_boxitem, db_boxship (+41 more) | 46 |
| db_orderitemdep | db_customer, db_department, db_employee, db_order, db_orderitem (+2 more) | 7 |
| db_orderiteminv | db_accounttype, db_bom, db_box, db_boxitem, db_boxship (+20 more) | 25 |
| db_orderitemlistprompt | db_orderitem, db_orderitemdep, db_product | 3 |
| db_orderitemprod | db_accounttype, db_bom, db_box, db_boxitem, db_boxship (+18 more) | 23 |
| db_orderitempromo | db_customer, db_order | 2 |
| db_orderitemvar | db_bom, db_box, db_boxitem, db_boxship, db_color (+8 more) | 13 |
| db_ordernotes | db_customer, db_loginid, db_mfgitem, db_order, db_orderitem (+2 more) | 7 |
| db_orderprint | db_bom, db_box, db_boxitem, db_boxship, db_color (+8 more) | 13 |
| db_ordersalesperson | db_cash, db_customer, db_customersalesperson, db_invoiceitem, db_order (+3 more) | 8 |
| db_po | db_ap, db_apitem, db_box, db_boxship, db_customer (+24 more) | 29 |
| db_poitem | db_ap, db_apitem, db_apitemgl, db_loginid, db_order (+14 more) | 19 |
| db_ponotes | db_loginid, db_order, db_po, db_vendor | 4 |
| db_priceruledetail | db_pricerule | 1 |
| db_priceruledetailvalue | db_pricerule | 1 |
| db_printroute | db_bom, db_department, db_mfgitem, db_model, db_prod (+1 more) | 6 |
| db_printroutelabel | db_bom, db_mfg, db_mfgitem, db_product | 4 |
| db_product | db_bom, db_box, db_boxship, db_color, db_customer (+26 more) | 31 |
| db_product_po | db_product | 1 |
| db_productgroup | db_product, db_productgroupitem | 2 |
| db_productgroupitem | db_box, db_boxitem, db_boxship, db_customer, db_department (+6 more) | 11 |
| db_productprompt | db_bom, db_bomcomponent, db_color, db_product, db_productpromptvalue (+4 more) | 9 |
| db_productpromptvalue | db_bom, db_box, db_boxitem, db_boxship, db_color (+9 more) | 14 |
| db_promptrule | db_promptruledetail, db_promptruledetailvalue | 2 |
| db_reasoncode | db_gl | 1 |
| db_recordchangelog | db_customer, db_loginid, db_stock, db_stockbalance, db_stockbalancecomp (+1 more) | 6 |
| db_return | db_box, db_boxship, db_customer, db_invoiceitem, db_orderitem (+3 more) | 8 |
| db_salescommissionlog | db_ap, db_customer, db_invoice, db_invoiceitem, db_ordersalespersoncharge (+3 more) | 8 |
| db_salesperson | db_customer, db_customernotes, db_customersalesperson, db_event, db_eventtype (+13 more) | 18 |
| db_shipto | db_customer | 1 |
| db_site | db_customer, db_customersalesperson, db_event, db_eventtype, db_invoice (+11 more) | 16 |
| db_standardentries | db_ap, db_apitem, db_gl, db_journal, db_journalitemdetail (+6 more) | 11 |
| db_status | db_order, db_orderitem, db_product, db_vendor | 4 |
| db_stock | db_ap, db_apitem, db_bom, db_bomcomponent, db_box (+26 more) | 31 |
| db_stockbalance | db_customer, db_order, db_orderitem, db_stock, db_stockbalancecomp (+2 more) | 7 |
| db_stockbalancecomp | db_cid, db_customer, db_mfgitem, db_order, db_orderitem (+8 more) | 13 |
| db_stockhistory | db_stock, db_stockbalance, db_stockbalancecomp, db_stockclass | 4 |
| db_stocktranx | db_loginid, db_orderitem, db_po, db_poitem, db_stock (+4 more) | 9 |
| db_stocktranxreason | db_mfg, db_mfgitem, db_orderitem, db_product, db_stock (+3 more) | 8 |
| db_tax | db_customer, db_gl, db_invoice, db_invoiceitem, db_salesperson (+1 more) | 6 |
| db_teammember | db_loginid, db_team | 2 |
| db_textmessagetrigger | db_template, db_textmessagetriggeritem | 2 |
| db_uom | db_stock | 1 |
| db_vendor | db_ap, db_apitem, db_check, db_edipoack, db_order (+11 more) | 16 |
| db_vendorcustomer | db_customer, db_vendor, db_vendorcustomerdetail | 3 |
| db_vendordiscount | db_stock | 1 |
| db_vendorstock | db_stock, db_stockbalance, db_vendor | 3 |
| db_warehouse | db_customer, db_customersalesperson, db_orderitem, db_status | 4 |
| db_wipitem | db_department, db_employee, db_loginid, db_orderitem | 4 |
| db_xmlstatus | db_po | 1 |
| db_zip | db_invoice | 1 |
| pi | db_poitem, db_stock | 2 |
| tmp_orderitema_wo | db_color, db_orderitem, db_productprompt, db_productpromptvalue | 4 |
| wip_orderentity | db_chartofaccounts, db_gl, db_order, wip_invoice, wip_journalitemdetail | 5 |

## Most Common Table Combinations
| Rank | Tables | Usage Count |
|------|--------|-------------|
| 1 | db_order, db_orderitem | 247 |
| 2 | db_customer, db_order, db_orderitem, db_product | 128 |
| 3 | db_order, db_orderitem, db_product | 123 |
| 4 | db_customer, db_order, db_orderitem | 86 |
| 5 | db_customer, db_order | 77 |
| 6 | db_customer, db_order, db_orderitem, db_product, db_status | 55 |
| 7 | db_customer, db_order, db_ordersalesperson, db_salesperson, db_status | 52 |
| 8 | db_box, db_boxitem, db_boxship, db_customer, db_mfg, db_mfgitem, db_order, db_orderitem, db_product | 39 |
| 9 | db_model, db_order, db_orderitem | 37 |
| 10 | db_box, db_boxitem, db_boxship, db_customer, db_mfg, db_mfgitem, db_orderitem, db_product | 36 |
| 11 | db_stock, db_stockbalancecomp | 34 |
| 12 | db_customer, db_order, db_orderitem, db_orderitemprod, db_product, db_productgroup | 34 |
| 13 | db_accounttype, db_customer, db_order, db_orderitem, db_orderitemprod, db_product, db_productgroup | 32 |
| 14 | db_order, db_orderitem, db_orderiteminv, db_orderitemprod | 31 |
| 15 | db_order, db_ordersalesperson, db_salesperson | 31 |

## Business Function Categories
| Category | Query Count | Percentage |
|----------|-------------|------------|
| customer_management | 2367 | 38.9% |
| financial | 640 | 10.5% |
| general | 498 | 8.2% |
| inventory_management | 855 | 14.0% |
| order_management | 3981 | 65.4% |
| production | 1 | 0.0% |
| reporting | 2603 | 42.8% |
| sales_reporting | 772 | 12.7% |
| simple_lookup | 832 | 13.7% |
| vendor_management | 254 | 4.2% |

## Query Complexity Distribution
| Complexity Level | Count | Percentage |
|------------------|-------|------------|
| Simple (1-3) | 1043 | 17.1% |
| Medium (4-10) | 1361 | 22.4% |
| Complex (11-20) | 1731 | 28.4% |
| Very Complex (21+) | 1951 | 32.1% |

## Selected Representative Queries (75)
| Rank | Main Table | Tables Count | Complexity | Categories |
|------|------------|--------------|------------|------------|
| 1 | db_order | 15 | 34 | order_management, customer_management, reporting, inventory_management |
| 2 | db_order | 13 | 30 | order_management, customer_management, reporting, inventory_management |
| 3 | db_order | 13 | 30 | order_management, customer_management, reporting, inventory_management |
| 4 | db_order | 14 | 30 | order_management, customer_management, inventory_management |
| 5 | db_order | 12 | 27 | order_management, customer_management, inventory_management |
| 6 | db_order | 13 | 26 | order_management, customer_management, inventory_management |
| 7 | db_order | 11 | 22 | order_management, customer_management, inventory_management |
| 8 | db_order | 11 | 24 | order_management, customer_management, inventory_management |
| 9 | db_order | 13 | 26 | order_management, customer_management, inventory_management |
| 10 | db_order | 11 | 23 | order_management, customer_management, inventory_management |
| 11 | db_order | 11 | 23 | order_management, customer_management, inventory_management |
| 12 | db_order | 13 | 26 | order_management, customer_management, inventory_management |
| 13 | db_order | 11 | 23 | order_management, customer_management, inventory_management |
| 14 | db_order | 13 | 35 | order_management, customer_management, reporting, inventory_management |
| 15 | db_order | 13 | 30 | order_management, customer_management, reporting |
| 16 | db_invoice | 5 | 23 | reporting, financial, sales_reporting |
| 17 | db_product | 5 | 9 | inventory_management |
| 18 | db_invoice | 4 | 19 | reporting, financial |
| 19 | db_printroutelabel | 5 | 9 | general |
| 20 | db_invoice | 4 | 10 | reporting, financial, sales_reporting |
... and 55 more queries

## Recommendations
Based on the analysis, the following query patterns would be most valuable for documentation:

1. **Order Management Queries**: Focus on db_order + db_orderitem joins
2. **Customer Reporting**: db_customer with aggregations
3. **Multi-table Joins**: Demonstrate complex relationships
4. **Common Business Functions**: Inventory, sales, financial reporting
5. **Graduated Complexity**: From simple lookups to complex analytical queries