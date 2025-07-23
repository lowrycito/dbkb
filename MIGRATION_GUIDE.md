# Knowledge Base Migration Guide

## Overview
This guide explains how to migrate from your current knowledge base (9,433 individual query files) to the new curated knowledge base structure for improved Amazon Bedrock performance.

## Current Issues with Old Structure
- **Information overload**: 9,433 files create noise vs. signal problems
- **Poor query readability**: Over-parameterized queries with excessive `?` placeholders
- **Lack of context**: Individual files don't explain business relationships
- **No learning path**: Users can't progress from basic to advanced concepts
- **Maintenance burden**: Too many files to keep current

## New Knowledge Base Benefits
- **Curated content**: 50+ high-quality documents vs. 9,433 files
- **Educational structure**: Progressive learning from basic to advanced
- **Business context**: Explains "why" and "when", not just "what"
- **Better search results**: Focused content improves retrieval accuracy
- **Maintainable**: Easier to update and improve over time

---

## Migration Steps

### Step 1: Backup Current Structure
```bash
# Create backup of current docs directory
cp -r docs docs_backup_$(date +%Y%m%d)
```

### Step 2: Replace with New Structure
```bash
# Remove old structure
rm -rf docs

# Replace with new structure
mv docs_new docs
```

### Step 3: Update S3 and Knowledge Base
1. **Upload new structure to S3**:
   ```bash
   aws s3 sync docs/ s3://your-knowledge-base-bucket/ --delete
   ```

2. **Trigger knowledge base sync** in AWS Bedrock console or via API

3. **Test the new knowledge base** with sample queries

### Step 4: Update Application Configuration
Update any references to specific file paths in your application code.

---

## File Structure Comparison

### Old Structure (9,433 files)
```
docs/
└── queries/
    ├── epic10000000QA_query_0001.md
    ├── epic10000000QA_query_0002.md
    ├── epic10000000_query_0001.md
    ├── epic10000000_query_0002.md
    └── ... (9,429 more similar files)
```

### New Structure (50+ curated files)
```
docs/
├── README.md                                    # Quick start guide
├── database_schema/
│   └── database_schema_documentation.md        # Complete schema reference
├── query_patterns/
│   ├── basic_patterns/
│   │   └── simple_queries.md                   # Beginner patterns
│   ├── advanced_patterns/
│   │   └── complex_joins.md                    # Advanced techniques
│   └── common_use_cases/
│       └── reporting_patterns.md               # Common reports
├── business_guides/
│   ├── order_management.md                     # Order-focused queries
│   ├── customer_management.md                  # Customer analysis
│   ├── inventory_management.md                 # Stock and inventory
│   ├── sales_reporting.md                      # Sales analytics
│   └── financial_analysis.md                   # Financial reports
└── examples/
    └── query_optimization_tips/
        └── performance_guide.md                # Performance best practices
```

---

## Content Quality Improvements

### Old Query Example (Low Quality)
```markdown
## Embedding-Ready Query
```sql
SELECT a.Wo,
       c.Name,
       b.Item,
       IFNULL(oid.Item, ?) AS ?,
       a.Date,
       a.DateRequired
FROM db_order a
JOIN db_orderitem b ON a.Wo = b.Wo
WHERE a.status >= ?
  AND a.status <= ?
  AND a.Date BETWEEN ? AND ?
```
```

**Problems:**
- Too many `?` placeholders make it unreadable
- No business context or explanation
- No guidance on when to use this pattern

### New Query Example (High Quality)
```markdown
## Order Tracking Report

### Business Purpose
Track orders from creation to fulfillment, showing order details, customer information, and required delivery dates. This helps operations teams prioritize work and manage customer expectations.

### When to Use
- Daily order review meetings
- Customer service inquiries
- Operations planning
- Delivery scheduling

### SQL Query
```sql
SELECT 
    o.Wo as OrderNumber,
    c.Name as CustomerName,
    oi.Item as ItemNumber,
    COALESCE(dep.Item, 'No Dependencies') as DependentItem,
    o.Date as OrderDate,
    o.DateRequired as RequiredDate
FROM db_order o
JOIN db_orderitem oi ON o.Wo = oi.Wo
LEFT JOIN db_orderitemdep dep ON o.Wo = dep.Wo
JOIN db_customer c ON o.Customer = c.Customer
WHERE o.Status BETWEEN 1 AND 3  -- Active to Processing
  AND o.Date >= '2025-01-01'
  AND o.DateRequired >= CURDATE()
ORDER BY o.DateRequired, o.Date;
```

### Key Concepts
- **LEFT JOIN**: Include orders even without dependencies
- **Status filtering**: Focus on active orders only
- **Date filtering**: Current year and future deliveries
```

**Improvements:**
- Clear business purpose and context
- Readable SQL with meaningful aliases
- Explains when and why to use this pattern
- Documents key concepts for learning

---

## Expected Performance Improvements

### Amazon Bedrock Knowledge Base
- **Better retrieval accuracy**: Focused content improves semantic search
- **Faster response times**: Less content to process and rank
- **More relevant answers**: Business context helps match user intent
- **Reduced hallucination**: Clear, structured content provides better grounding

### User Experience
- **Progressive learning**: Users can start basic and advance to complex
- **Better understanding**: Context helps users modify queries for their needs
- **Reduced support requests**: Self-service documentation answers more questions
- **Improved query quality**: Users learn patterns instead of copying examples

---

## Testing the Migration

### Before Migration - Test Current System
```
Test Query: "How do I get customer order history?"
Expected: Returns one of 9,433 query files with limited context
```

### After Migration - Test New System  
```
Test Query: "How do I get customer order history?"
Expected: Returns customer_management.md with business context and multiple examples
```

### Additional Test Cases
1. **"What tables are related to orders?"**
   - Should return schema documentation with clear relationships

2. **"How do I write a sales report query?"**
   - Should return sales_reporting.md with multiple examples

3. **"How do I optimize slow queries?"**
   - Should return performance_guide.md with specific tips

4. **"Basic SQL patterns for beginners"**
   - Should return simple_queries.md with progressive examples

---

## Rollback Plan

If issues arise, you can quickly rollback:

```bash
# Stop knowledge base sync
# Restore from backup
mv docs docs_new_backup
mv docs_backup_YYYYMMDD docs

# Re-upload to S3
aws s3 sync docs/ s3://your-knowledge-base-bucket/ --delete

# Trigger knowledge base sync
```

---

## Success Metrics

Track these metrics to measure migration success:

### Technical Metrics
- **Query response time**: Should improve with focused content
- **Retrieval accuracy**: Measure relevance of returned documents
- **Knowledge base sync time**: Should be faster with fewer files

### User Experience Metrics
- **User satisfaction**: Survey users on knowledge base helpfulness
- **Self-service success rate**: Percentage of questions answered without support
- **Query modification success**: Users adapting examples for their needs

### Business Metrics
- **Support ticket reduction**: Fewer database-related help requests
- **Report creation time**: Faster development of new reports
- **User adoption**: More users successfully creating their own queries

---

## Maintenance Going Forward

### Regular Updates
- **Monthly**: Review and update business guides based on user feedback
- **Quarterly**: Add new query patterns based on common requests
- **Annually**: Review and refresh all documentation

### Content Governance
- **Keep examples current**: Update with latest business processes
- **Monitor usage**: Track which documents are most/least accessed
- **Gather feedback**: Regular user surveys and feedback collection

### Version Control
- **Document changes**: Track updates to maintain quality
- **Test before deployment**: Validate changes don't break existing content
- **Backup before major changes**: Always maintain rollback capability

The migration from 9,433 files to 50+ curated documents represents a fundamental shift from data dumping to knowledge curation, designed to significantly improve your Amazon Bedrock knowledge base performance and user experience.