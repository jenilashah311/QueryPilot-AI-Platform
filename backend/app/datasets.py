from __future__ import annotations

import io
import re

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models import Workspace


def _sanitize_col(c: str) -> str:
    c = re.sub(r"[^a-zA-Z0-9_]+", "_", str(c).strip())
    return c.lower()[:63] or "col"


def _detect_and_read_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Detect file format and read accordingly. Supports CSV, XLSX, XLS."""
    filename_lower = filename.lower()
    
    # Try to determine format from filename
    if filename_lower.endswith(('.xlsx', '.xls')):
        try:
            # Try reading as Excel
            engine = 'openpyxl' if filename_lower.endswith('.xlsx') else 'xlrd'
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, engine=engine)
            return df
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")
    elif filename_lower.endswith('.csv'):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
            return df
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")
    else:
        # Try to auto-detect: attempt Excel first, then CSV
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, engine='openpyxl')
            return df
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes))
                return df
            except Exception as e:
                raise ValueError(f"Could not read file. Supported formats: CSV, XLSX, XLS. Error: {str(e)}")


def replace_dataset(db: Session, workspace: Workspace, file_bytes: bytes, filename: str) -> dict:
    """Load dataset from CSV or Excel file and store in database."""
    # Read file with format detection
    df = _detect_and_read_file(file_bytes, filename)
    
    # Validate that we have data
    if df.empty:
        raise ValueError("File contains no data")
    
    # Sanitize column names
    df.columns = [_sanitize_col(c) for c in df.columns]
    
    # Drop completely empty columns
    df = df.dropna(axis=1, how='all')
    
    schema = workspace.schema_name
    table = "analytics_primary"
    bind = db.get_bind()
    with bind.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table}"'))
        df.to_sql(
            table,
            con=conn,
            schema=schema,
            index=False,
            if_exists="replace",
            method="multi",
            chunksize=500,
        )
    
    # Get data type information for better query generation
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "column_types": dtypes,
        "table": table,
        "filename": filename,
    }


def list_columns(db: Session, workspace: Workspace) -> list[str]:
    try:
        insp = inspect(db.get_bind())
        if not insp.has_table("analytics_primary", schema=workspace.schema_name):
            return []
        cols = insp.get_columns("analytics_primary", schema=workspace.schema_name)
        return [c["name"] for c in cols]
    except Exception:
        return []

