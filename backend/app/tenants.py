from __future__ import annotations

import re
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Role, User, Workspace


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return (s or "workspace")[:60]


def schema_for_workspace(wid: uuid.UUID) -> str:
    return f"t_{str(wid).replace('-', '')[:24]}"


def create_workspace(db: Session, name: str, owner_email: str, password_hash: str) -> tuple[Workspace, User]:
    wid = uuid.uuid4()
    schema = schema_for_workspace(wid)
    slug_base = slugify(name)
    slug = slug_base
    n = 0
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        n += 1
        slug = f"{slug_base}-{n}"

    ws = Workspace(id=wid, name=name, slug=slug, schema_name=schema, plan="free")
    db.add(ws)
    db.flush()

    user = User(
        email=owner_email.lower(),
        hashed_password=password_hash,
        role=Role.admin,
        workspace_id=ws.id,
    )
    db.add(user)
    db.commit()
    db.refresh(ws)
    db.refresh(user)

    bind = db.get_bind()
    with bind.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    return ws, user
