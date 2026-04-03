from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app import oauth_google
from app.auth import create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.config import settings
from app.db import get_db, init_db
from app.datasets import list_columns, replace_dataset
from app.models import Role, User, Workspace
from app.query_engine import run_query
from app.tenants import create_workspace
from app import stripe_billing

app = FastAPI(title="AI Analytics SaaS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


class RegisterIn(BaseModel):
    workspace_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class QueryIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


@app.post("/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    ws, user = create_workspace(db, body.workspace_name, body.email.lower(), hash_password(body.password))
    token = create_access_token(user.id, ws.id, user.role)
    return TokenOut(access_token=token)


@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, user.workspace_id, user.role)
    return TokenOut(access_token=token)


@app.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.get(Workspace, user.workspace_id)
    return {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "workspace": {"id": str(ws.id), "name": ws.name, "slug": ws.slug, "plan": ws.plan} if ws else None,
    }


@app.post("/datasets/upload")
def upload_dataset(
    file: UploadFile = File(...),
    user: User = Depends(require_roles(Role.admin, Role.analyst)),
    db: Session = Depends(get_db),
):
    ws = db.get(Workspace, user.workspace_id)
    if not ws:
        raise HTTPException(400, "No workspace")
    raw = file.file.read()
    if len(raw) > 20_000_000:
        raise HTTPException(413, "File too large")
    meta = replace_dataset(db, ws, raw, file.filename or "data.csv")
    return meta


@app.get("/datasets/schema")
def dataset_schema(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.get(Workspace, user.workspace_id)
    if not ws:
        raise HTTPException(400, "No workspace")
    cols = list_columns(db, ws)
    return {
        "columns": cols,
        "table": "analytics_primary",
        "message": "Upload CSV, XLSX, or XLS files. Any data structure is supported.",
    }


@app.post("/query")
def natural_query(
    body: QueryIn,
    user: User = Depends(require_roles(Role.admin, Role.analyst)),
    db: Session = Depends(get_db),
):
    ws = db.get(Workspace, user.workspace_id)
    if not ws:
        raise HTTPException(400, "No workspace")
    try:
        return run_query(db, ws, body.question)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/query/capabilities")
def query_capabilities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns information about supported query types and capabilities."""
    return {
        "supported_query_types": [
            "aggregation (SUM, AVG, COUNT, MIN, MAX)",
            "filtering (WHERE conditions)",
            "grouping (GROUP BY)",
            "sorting (ORDER BY)",
            "comparison (multiple columns)",
            "trend analysis (time-based)",
            "top/bottom analysis",
            "distinct values",
            "complex joins",
            "statistical queries",
        ],
        "supported_file_formats": ["CSV", "XLSX", "XLS"],
        "supported_databases": ["PostgreSQL"],
        "example_questions": [
            "How many records are in the dataset?",
            "What is the average value by category?",
            "Show me the top 5 products by sales",
            "Compare sales by region",
            "What is the trend of revenue over time?",
            "Which department has the highest cost?",
            "Show me distinct values in the region column",
            "Calculate the total revenue by product category",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}


app.include_router(oauth_google.router, prefix="/oauth", tags=["oauth"])
app.include_router(stripe_billing.router, prefix="/billing", tags=["billing"])
