# Project 4: Testing & Validation Guide

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/jenilshah/Documents/3\ project/project-4-fullstack-react-ai-saas/backend
pip install -r requirements.txt
```

### 2. Start the Backend
```bash
# With Docker
docker-compose up backend

# Or locally
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Test File Upload (Excel)

#### Upload XLSX File
```bash
curl -X POST "http://localhost:8000/datasets/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_data.xlsx"
```

#### Upload CSV File
```bash
curl -X POST "http://localhost:8000/datasets/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_data.csv"
```

#### Expected Response
```json
{
  "rows": 1000,
  "columns": ["id", "name", "category", "revenue", "date"],
  "column_types": {
    "id": "int64",
    "name": "object",
    "category": "object",
    "revenue": "float64",
    "date": "object"
  },
  "table": "analytics_primary",
  "filename": "sample_data.xlsx"
}
```

### 4. Test Query Generation

#### Count Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many records are in the dataset?"}'
```

#### Aggregation Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total revenue by category?"}'
```

#### Top N Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me the top 10 products by revenue"}'
```

#### Trend Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the revenue trend by month?"}'
```

### 5. Check Capabilities
```bash
curl -X GET "http://localhost:8000/query/capabilities" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Test Cases

### Test 1: Multiple File Formats
- [ ] Upload CSV file → Verify data loads correctly
- [ ] Upload XLSX file → Verify data loads correctly
- [ ] Upload XLS file → Verify data loads correctly
- [ ] Upload invalid format → Verify error message

### Test 2: Query Types
- [ ] Aggregation (SUM, AVG, COUNT, MIN, MAX)
- [ ] Grouping (GROUP BY multiple columns)
- [ ] Filtering (WHERE clauses)
- [ ] Sorting (ORDER BY)
- [ ] Top/Bottom (LIMIT with ORDER BY)
- [ ] Trending (Date-based aggregation)
- [ ] Complex (Multiple joins, subqueries)

### Test 3: Edge Cases
- [ ] Empty file → Should return error
- [ ] File with special characters in column names → Should sanitize
- [ ] NULL values in data → Should handle properly
- [ ] Very large files (10MB+) → Should handle efficiently
- [ ] Question with ambiguous columns → Should handle gracefully

### Test 4: Data Integrity
- [ ] Data types preserved after upload
- [ ] Column names sanitized correctly
- [ ] Row counts match original
- [ ] No data loss during conversion

### Test 5: Performance
- [ ] Query execution < 2 seconds for typical queries
- [ ] Caching works (same question twice should be faster)
- [ ] Large result sets paginated properly
- [ ] Memory usage stable with repeated queries

## Sample Test Data

### CSV Example (sample_data.csv)
```csv
order_id,customer_name,category,revenue,order_date,region
1001,Alice Smith,Electronics,1500.00,2024-01-15,North
1002,Bob Johnson,Clothing,800.00,2024-01-18,South
1003,Carol White,Electronics,2200.00,2024-02-10,East
1004,David Brown,Home,450.00,2024-02-14,West
1005,Emma Davis,Electronics,1800.00,2024-03-05,North
```

### Excel Example (sample_data.xlsx)
Create an Excel file with the same structure as CSV above.

## Debugging

### Enable Verbose Logging
```bash
# In .env or environment
SQLALCHEMY_ECHO=True
LOG_LEVEL=DEBUG
```

### Check Database Connection
```bash
curl -X GET "http://localhost:8000/health"
```

### Verify Schema Creation
```sql
-- Connect to PostgreSQL
psql -U postgres -h localhost -d ai_analytics_saas

-- List schemas
\dn

-- Check table
SELECT * FROM information_schema.tables 
WHERE table_schema = 'workspace_schema_name' 
AND table_name = 'analytics_primary';
```

### Monitor Query Execution
```sql
-- Enable query logging
SET log_statement = 'all';
SET log_duration = on;

-- Run query
SELECT * FROM analytics_primary LIMIT 10;
```

## Common Issues & Solutions

### Issue: "openpyxl not found"
```bash
pip install openpyxl==3.11.0
```

### Issue: "xlrd not found"
```bash
pip install xlrd==2.0.1
```

### Issue: "Could not read file"
- Check file format is CSV, XLSX, or XLS
- Verify file is not corrupted
- Try opening file in Excel/Calc to validate

### Issue: "Upload a CSV first" (old error message)
- Update to latest code version
- Clear browser cache
- Restart backend server

### Issue: Query returns no results
- Verify data was uploaded successfully
- Check column names in schema
- Try simpler query first: "How many records?"

### Issue: Permission denied on database
- Verify PostgreSQL user has CREATE permissions
- Check workspace schema exists
- Verify DATABASE_URL is correct

## Automation Testing

### Using Python
```python
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "your_token_here"

# Test file upload
with open("sample_data.xlsx", "rb") as f:
    files = {"file": f}
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/datasets/upload",
        files=files,
        headers=headers
    )
    print("Upload response:", response.json())

# Test query
query = {"question": "How many records are in the dataset?"}
response = requests.post(
    f"{BASE_URL}/query",
    json=query,
    headers={"Authorization": f"Bearer {TOKEN}"}
)
print("Query response:", response.json())
```

### Using Playwright (End-to-End)
See `frontend/e2e/smoke.spec.ts` for E2E test examples.

## Performance Benchmarks

Expected performance on typical hardware:

| Operation | Time | Notes |
|-----------|------|-------|
| Upload 1MB CSV | 0.5s | Sequential insert |
| Upload 5MB XLSX | 2s | Index creation |
| Simple COUNT query | 0.1s | Cached after first hit |
| GROUP BY 10k rows | 0.3s | Aggregation |
| LIMIT 1000 query | 0.2s | Large result set |

## Rollback Instructions

If issues occur after update:

1. **Restore old requirements.txt**
   ```bash
   git checkout backend/requirements.txt
   ```

2. **Restore old datasets.py**
   ```bash
   git checkout backend/app/datasets.py
   ```

3. **Restart services**
   ```bash
   docker-compose down
   docker-compose up backend
   ```

## Sign-Off Checklist

- [ ] All file formats upload successfully
- [ ] Data integrity verified after upload
- [ ] All query types generate correct SQL
- [ ] Results cached properly
- [ ] Error messages are helpful
- [ ] Performance acceptable
- [ ] No breaking changes to existing API
- [ ] Documentation updated
- [ ] Tests passing
- [ ] Ready for production

---

**Last Updated**: 2024  
**Tested On**: Python 3.11, PostgreSQL 14+  
**Compatibility**: All major operating systems
