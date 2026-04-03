from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

import redis
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.datasets import list_columns
from app.demo_sql import build_demo_sql, demo_insight
from app.models import Workspace


def _llm() -> ChatOpenAI:
    kwargs: dict[str, object] = {
        "model": settings.openai_model,
        "temperature": 0,
        "api_key": settings.openai_api_key or None,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if settings.openai_http_referer:
        kwargs["default_headers"] = {
            "HTTP-Referer": settings.openai_http_referer,
            "X-Title": "AI Analytics SaaS",
        }
    return ChatOpenAI(**kwargs)


def _llm_insight() -> ChatOpenAI:
    kwargs: dict[str, object] = {
        "model": settings.openai_model,
        "temperature": 0.3,
        "api_key": settings.openai_api_key or None,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if settings.openai_http_referer:
        kwargs["default_headers"] = {
            "HTTP-Referer": settings.openai_http_referer,
            "X-Title": "AI Analytics SaaS",
        }
    return ChatOpenAI(**kwargs)


def _get_column_info(db: Session, workspace: Workspace) -> dict[str, str]:
    """Get data types and sample values for all columns."""
    schema = workspace.schema_name
    schema_esc = schema.replace('"', '""')
    col_info = {}
    
    try:
        with db.get_bind().connect() as conn:
            # Get column info
            info_sql = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = '{schema_esc}' 
                AND table_name = 'analytics_primary'
                ORDER BY ordinal_position
            """)
            for row in conn.execute(info_sql).fetchall():
                col_info[row[0]] = row[1]
    except Exception:
        pass
    
    return col_info


def _detect_chart_type(rows: list[dict], columns: list[str], sql: str) -> dict[str, Any]:
    """
    Intelligently detect the best chart type based on query results.
    Returns chart_type and chart_config for frontend rendering.
    """
    if not rows or not columns:
        return {"chart_type": "none", "chart_config": {}}
    
    # Count columns and their types
    num_cols = len(columns)
    row_count = len(rows)
    sql_lower = sql.lower()
    
    # Analyze column data types and content
    first_row = rows[0]
    numeric_cols = []
    text_cols = []
    date_cols = []
    
    for col in columns:
        val = first_row.get(col)
        if val is None:
            continue
        
        val_type = type(val).__name__
        col_lower = col.lower()
        
        # Check if column looks like a date
        if isinstance(val, str) and any(x in col_lower for x in ['date', 'time', 'month', 'year', 'period']):
            date_cols.append(col)
        elif val_type in ('int', 'float', 'Decimal'):
            numeric_cols.append(col)
        else:
            text_cols.append(col)
    
    # Single metric (COUNT, SUM, AVG, etc.)
    if num_cols == 1 and numeric_cols:
        return {
            "chart_type": "metric",
            "chart_config": {
                "value_col": columns[0],
                "format": "number"
            }
        }
    
    # Time series (has date + numeric)
    if date_cols and numeric_cols:
        return {
            "chart_type": "line",
            "chart_config": {
                "x_axis": date_cols[0],
                "y_axis": numeric_cols[0],
                "title": f"{numeric_cols[0]} over {date_cols[0]}"
            }
        }
    
    # Grouped data (text + numeric) - bar chart
    if text_cols and numeric_cols:
        # Check if it's a top N query
        if row_count <= 20 and ("top" in sql_lower or "limit" in sql_lower or "order by" in sql_lower):
            return {
                "chart_type": "bar",
                "chart_config": {
                    "x_axis": text_cols[0],
                    "y_axis": numeric_cols[0],
                    "title": f"{numeric_cols[0]} by {text_cols[0]}"
                }
            }
        # Multiple numeric columns - use column chart
        elif len(numeric_cols) > 1:
            return {
                "chart_type": "column",
                "chart_config": {
                    "x_axis": text_cols[0],
                    "y_axis": numeric_cols[:2],
                    "title": f"Comparison by {text_cols[0]}"
                }
            }
        # Default grouped - bar chart
        else:
            return {
                "chart_type": "bar",
                "chart_config": {
                    "x_axis": text_cols[0],
                    "y_axis": numeric_cols[0],
                    "title": f"{numeric_cols[0]} by {text_cols[0]}"
                }
            }
    
    # Multiple numeric columns (no grouping) - scatter or area
    if len(numeric_cols) >= 2:
        return {
            "chart_type": "scatter",
            "chart_config": {
                "x_axis": numeric_cols[0],
                "y_axis": numeric_cols[1],
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}"
            }
        }
    
    # Only text columns - show as tags/word cloud
    if text_cols and not numeric_cols:
        return {
            "chart_type": "tags",
            "chart_config": {
                "column": text_cols[0],
                "count": min(row_count, 50)
            }
        }
    
    # Multiple text columns - comparison table
    if len(text_cols) > 1:
        return {
            "chart_type": "table",
            "chart_config": {}
        }
    
    # Default to table
    return {
        "chart_type": "table",
        "chart_config": {}
    }


def _allowed_sql(sql: str) -> bool:
    """Validate SQL is safe (read-only SELECT only)."""
    s = sql.strip().lower()
    if not s.startswith("select"):
        return False
    core = s.rstrip().rstrip(";")
    if ";" in core:
        return False
    # Block dangerous SQL commands
    banned = (" insert ", " update ", " delete ", " drop ", " alter ", " create ", " truncate ", "--", "/*", "*/")
    padded = f" {core} "
    return not any(b in padded for b in banned)


def _cache_key(workspace_id: str, question: str) -> str:
    h = hashlib.sha256(f"{workspace_id}:{question}".encode()).hexdigest()
    return f"qcache:{h}"


def run_query(
    db: Session,
    workspace: Workspace,
    question: str,
    use_cache: bool = True,
) -> dict[str, Any]:
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    ck = _cache_key(str(workspace.id), question)
    if use_cache:
        hit = r.get(ck)
        if hit:
            return json.loads(hit)

    schema = workspace.schema_name
    cols = list_columns(db, workspace)
    if not cols:
        raise ValueError("Upload data first (CSV, XLSX, or XLS file).")

    sql = ""
    if settings.demo_mode or not settings.openai_api_key:
        # In demo mode, make filters match values that actually exist in the CSV.
        # This avoids hardcoding Sales/HR/etc.
        dept_col = next((c for c in cols if "department" in c.lower() or c.lower() == "dept" or "dept" in c.lower()), None)
        job_col = next(
            (
                c
                for c in cols
                if "job_level" in c.lower() or "joblevel" in c.lower() or ("job" in c.lower() and "level" in c.lower())
            ),
            None,
        )

        dept_values: list[str] | None = None
        job_values: list[str] | None = None

        # Fetch distinct values only when the corresponding columns exist.
        schema_esc = schema.replace('"', '""')
        with db.get_bind().connect() as conn:
            if dept_col:
                v_sql = text(f'SELECT DISTINCT "{dept_col}" FROM "{schema_esc}".analytics_primary LIMIT 200')
                dept_values = [str(r[0]) for r in conn.execute(v_sql).fetchall() if r[0] is not None]
            if job_col:
                v_sql = text(f'SELECT DISTINCT "{job_col}" FROM "{schema_esc}".analytics_primary LIMIT 200')
                job_values = [str(r[0]) for r in conn.execute(v_sql).fetchall() if r[0] is not None]

        sql = build_demo_sql(schema, cols, question, dept_values=dept_values, job_values=job_values)
    else:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key or "")
        llm = _llm()
        q_lower = question.lower()
        
        # Detect question patterns
        wants_count = (
            ("how many" in q_lower)
            or ("number of" in q_lower)
            or ("count" in q_lower)
        ) and not (
            "avg" in q_lower
            or "average" in q_lower
            or "mean" in q_lower
        )
        wants_trend = any(word in q_lower for word in ["trend", "over time", "by month", "by year", "by date", "timeline", "progression"])
        wants_comparison = any(word in q_lower for word in ["compare", "vs", "versus", "difference", "better", "worse"])
        wants_top = any(word in q_lower for word in ["top", "highest", "lowest", "best", "worst", "most", "least"])
        
        count_instruction = (
            "If the user asks for how many / count / number of, use COUNT(*) as the main measure "
            "(e.g. alias it as row_count or count_value). Do not use AVG() for count questions."
            if wants_count
            else ""
        )
        
        trend_instruction = (
            "For trend analysis, use ORDER BY for time-based columns and GROUP BY to aggregate by period. "
            "Include time/date columns for timeline visibility."
            if wants_trend
            else ""
        )
        
        col_info = _get_column_info(db, workspace)
        col_info_str = ", ".join([f"{col} ({dtype})" for col, dtype in col_info.items()]) if col_info else ", ".join(cols)
        
        sys = SystemMessage(
            content=(
                f'You are an expert SQL analyst. Write a single PostgreSQL SELECT query for schema "{schema}" table "analytics_primary". '
                f'Quote identifiers with double quotes. '
                f'Columns with types: {col_info_str}. '
                f'Handle NULL values appropriately (use COALESCE, IS NULL, etc). '
                f'Use aggregate functions (COUNT, SUM, AVG, MIN, MAX) when appropriate. '
                f'Use GROUP BY, ORDER BY, HAVING, DISTINCT, LIMIT as needed for complete analysis. '
                f'For filtering, use appropriate WHERE clauses. '
                f'{count_instruction} '
                f'{trend_instruction} '
                f'Always optimize for accuracy and performance. '
                f'Reply ONLY with SQL, no markdown or explanation.'
            )
        )
        sql = llm.invoke([sys, HumanMessage(content=question)]).content.strip()
        sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()

        # Safety guard: if the user asked for count/how-many, reject AVG()-based SQL
        # and fall back to the rule-based generator.
        if wants_count and "avg(" in sql.lower():
            sql = build_demo_sql(schema, cols, question)

    if not _allowed_sql(sql):
        raise ValueError("Generated SQL failed safety checks (read-only SELECT only).")

    with db.get_bind().connect() as conn:
        result = conn.execute(text(sql))
        rows = [dict(row._mapping) for row in result.fetchall()]

    if settings.demo_mode or not settings.openai_api_key:
        insight = demo_insight(rows, question)
    else:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key or "")
        llm = _llm_insight()
        insight = llm.invoke(
            [
                SystemMessage(content="Two short sentences summarizing the tabular result for a business user."),
                HumanMessage(content=json.dumps({"question": question, "sample_rows": rows[:8]}, default=str)),
            ]
        ).content.strip()

    columns = list(rows[0].keys()) if rows else []
    chart_info = _detect_chart_type(rows, columns, sql)
    
    out = {
        "sql": sql,
        "rows": rows,
        "insight": insight,
        "columns": columns,
        "chart_type": chart_info["chart_type"],
        "chart_config": chart_info["chart_config"],
    }
    r.setex(ck, 300, json.dumps(out, default=str))
    return out
