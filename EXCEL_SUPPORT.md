# Project 4: Global SQL Query System with Excel Support

## Overview
This project has been enhanced to support all types of questions on any data present in Excel files (.xlsx, .xls) or CSV files, with SQL-based query generation for comprehensive data analysis.

## Key Features

### 1. **Multi-Format File Support**
- ✅ CSV (.csv) - Original format
- ✅ Excel (.xlsx) - Modern Excel format
- ✅ Excel (.xls) - Legacy Excel format
- ✅ Auto-detection - Automatically detects file format
- ✅ Data validation - Ensures data integrity before storing

### 2. **Global Query System**
The system can handle ANY type of question asked in the chat, including:

#### Aggregation Queries
- "How many records are in the dataset?"
- "What is the average value by category?"
- "Calculate total revenue by region"

#### Top/Bottom Analysis
- "Show me the top 5 products by sales"
- "What are the bottom 3 performing departments?"
- "List the highest cost items"

#### Comparison Queries
- "Compare sales by region"
- "What's the difference between Q1 and Q2?"
- "Which product has better performance?"

#### Trend Analysis
- "What is the trend of revenue over time?"
- "Show me the progression by month"
- "How has the metric changed over the year?"

#### Filtering & Sorting
- "Show all records where region is North"
- "Sort employees by salary in descending order"
- "Filter data by date range"

#### Complex Analysis
- "Find correlations between columns"
- "Identify patterns in the data"
- "Show statistical summaries"

### 3. **Intelligent Query Generation**
The system uses LLM (Large Language Model) to:
- Understand natural language questions
- Generate optimized PostgreSQL queries
- Handle edge cases (NULL values, data types, etc.)
- Automatically detect question patterns (count, trend, comparison)
- Fall back to rule-based generation in demo mode

### 4. **Enhanced Error Handling**
- ✅ Empty file validation
- ✅ Column name sanitization
- ✅ Data type preservation
- ✅ Safe SQL validation (read-only SELECT only)
- ✅ Detailed error messages

## Technical Implementation

### Backend Changes

#### 1. **requirements.txt**
Added dependencies:
```
openpyxl==3.11.0  # Excel .xlsx support
xlrd==2.0.1       # Excel .xls support
```

#### 2. **app/datasets.py** - Enhanced with Excel Support
```python
def _detect_and_read_file(file_bytes: bytes, filename: str) -> pd.DataFrame
```
Features:
- Auto-detects file format from filename or content
- Supports CSV, XLSX, XLS formats
- Sanitizes column names for SQL compatibility
- Validates data before storage
- Returns column type information

#### 3. **app/query_engine.py** - Advanced Query Generation
Enhanced functions:
- `_get_column_info()` - Retrieves data types for better SQL generation
- Detects question patterns:
  - Count queries
  - Trend analysis questions
  - Comparison queries
  - Top/bottom analysis
- Improved LLM prompt with:
  - Column type information
  - Appropriate SQL function guidance
  - NULL value handling strategies
  - Performance optimization tips

#### 4. **app/main.py** - New Endpoints
Added endpoints:
- `GET /datasets/schema` - Enhanced to show supported formats
- `GET /query/capabilities` - Lists all supported query types and examples

### Database Changes
- Single `analytics_primary` table per workspace schema
- Automatic schema creation and management
- Support for any column structure and data types

## Usage Examples

### 1. Upload Excel File
```bash
curl -X POST "http://localhost:8000/datasets/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.xlsx"
```

### 2. Ask Natural Language Question
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total revenue by product category?"}'
```

Response:
```json
{
  "sql": "SELECT product_category, SUM(revenue) as total_revenue FROM \"schema\".analytics_primary GROUP BY product_category ORDER BY total_revenue DESC",
  "rows": [
    {"product_category": "Electronics", "total_revenue": 150000},
    {"product_category": "Clothing", "total_revenue": 95000}
  ],
  "insight": "Electronics is the top performing category with $150,000 in revenue, while Clothing accounts for $95,000.",
  "columns": ["product_category", "total_revenue"]
}
```

### 3. Check Query Capabilities
```bash
curl -X GET "http://localhost:8000/query/capabilities" \
  -H "Authorization: Bearer <token>"
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React/TypeScript)                │
│                   (Chat Interface with File Upload)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    API Endpoints                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ /datasets/upload │  │ /query           │  │ /query/caps  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  Business Logic Layer                            │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  File Detection     │  │  Query Generation               │  │
│  │  - CSV              │  │  - LLM-based                    │  │
│  │  - XLSX             │  │  - Pattern detection            │  │
│  │  - XLS              │  │  - SQL optimization             │  │
│  └─────────────────────┘  └──────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  Data Layer                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         PostgreSQL Database                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  Workspace 1 │  │  Workspace 2 │  │  Workspace N │  │   │
│  │  │  Schema      │  │  Schema      │  │  Schema      │  │   │
│  │  │  - analytics │  │  - analytics │  │  - analytics │  │   │
│  │  │    _primary  │  │    _primary  │  │    _primary  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Supported Query Types

| Query Type | Example | SQL Generated |
|-----------|---------|---------------|
| Count | "How many records?" | SELECT COUNT(*) FROM table |
| Sum | "Total revenue?" | SELECT SUM(revenue) FROM table |
| Average | "Average price?" | SELECT AVG(price) FROM table |
| Group By | "Revenue by category?" | SELECT category, SUM(revenue) GROUP BY category |
| Top N | "Top 5 products?" | SELECT * FROM table ORDER BY sales DESC LIMIT 5 |
| Filter | "Sales over $1000?" | SELECT * FROM table WHERE sales > 1000 |
| Trend | "Revenue by month?" | SELECT DATE_TRUNC('month', date), SUM(revenue) GROUP BY DATE_TRUNC('month', date) |

## Configuration

### Environment Variables
```
OPENAI_API_KEY=sk-...       # Required for LLM-based query generation
OPENAI_MODEL=gpt-4o         # Default model
REDIS_URL=redis://...       # For caching results
DATABASE_URL=postgresql://..
DEMO_MODE=false             # Enable rule-based generation when true
```

### Demo Mode
When `DEMO_MODE=true` or no OpenAI key is provided:
- Uses rule-based SQL generation
- Works without API keys
- Limited to predefined patterns
- Better for testing

## Performance Optimization

### Caching
- Query results cached in Redis for 5 minutes
- Cache key based on workspace + question
- Automatic cache invalidation on new data

### Query Optimization
- Automatic LIMIT for large result sets
- Indexed columns for fast filtering
- Connection pooling for database efficiency

## Security Features

### SQL Safety
- Read-only SELECT queries only
- Blocks: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
- Quote identifiers to prevent injection
- Validates SQL before execution

### Data Privacy
- Per-workspace database schemas
- Row-level security through workspace isolation
- No cross-workspace data access

### File Upload Validation
- Max file size: 20MB
- Supported formats only: CSV, XLSX, XLS
- Column name sanitization
- Data type validation

## Troubleshooting

### Issue: "Could not read file"
**Solution**: Ensure file is in CSV, XLSX, or XLS format

### Issue: "Upload data first"
**Solution**: Upload a data file using `/datasets/upload` endpoint

### Issue: Query returns unexpected results
**Solution**: Check `/query/capabilities` for supported patterns, or refine the question

### Issue: Performance is slow
**Solution**: 
- Check Redis connection
- Consider LIMIT in question: "Show me first 100 records"
- Verify database indexes exist

## Future Enhancements

- [ ] Support for JSON/Parquet files
- [ ] Multi-sheet Excel handling
- [ ] Data transformation pipelines
- [ ] Advanced visualization options
- [ ] Query history and analytics
- [ ] Scheduled report generation
- [ ] Data quality checks
- [ ] ML-based anomaly detection

## API Documentation

### Endpoints Summary

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | /datasets/upload | Admin/Analyst | Upload data file |
| GET | /datasets/schema | All | Get dataset structure |
| POST | /query | Admin/Analyst | Ask question |
| GET | /query/capabilities | All | List capabilities |
| GET | /health | None | Health check |

## Support

For issues or questions:
1. Check the logs: `docker logs backend`
2. Verify database connection
3. Ensure OpenAI API key is set
4. Check file format compatibility

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Production Ready
