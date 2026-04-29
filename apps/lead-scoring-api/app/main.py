from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, select


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    api_token: str
    database_url: str


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Lead Scoring API"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        api_token=os.getenv("API_TOKEN", "dev-token"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
    )


settings = get_settings()


class RecordStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class Lead(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    name: str = SQLField(index=True, min_length=2, max_length=120)
    description: str | None = SQLField(default=None, max_length=500)
    owner: str | None = SQLField(default=None, max_length=80)
    status: RecordStatus = SQLField(default=RecordStatus.draft)
    created_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner: str | None = Field(default=None, max_length=80)
    status: RecordStatus = Field(default=RecordStatus.draft)


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner: str | None = Field(default=None, max_length=80)
    status: RecordStatus | None = None


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner: str | None
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
app = FastAPI(title=settings.app_name, version="1.1.0")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def verify_token(x_api_token: str | None = Header(default=None, alias="X-API-Token")) -> None:
    if x_api_token != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")


@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)


@app.get("/")
def index() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "api_prefix": settings.api_prefix,
    }


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready")
def health_ready() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready", "service": settings.app_name}


@app.post(f"{settings.api_prefix}/leads", response_model=LeadRead, dependencies=[Depends(verify_token)])
def create_record(payload: LeadCreate, session: Session = Depends(get_session)) -> Lead:
    record = Lead(**payload.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@app.get(f"{settings.api_prefix}/leads", response_model=list[LeadRead], dependencies=[Depends(verify_token)])
def list_records(
    status: RecordStatus | None = Query(default=None),
    owner: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Lead]:
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if owner:
        stmt = stmt.where(Lead.owner == owner)
    stmt = stmt.order_by(Lead.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@app.get(f"{settings.api_prefix}/leads/{{record_id}}", response_model=LeadRead, dependencies=[Depends(verify_token)])
def get_record(record_id: int, session: Session = Depends(get_session)) -> Lead:
    record = session.get(Lead, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.patch(f"{settings.api_prefix}/leads/{{record_id}}", response_model=LeadRead, dependencies=[Depends(verify_token)])
def update_record(record_id: int, payload: LeadUpdate, session: Session = Depends(get_session)) -> Lead:
    record = session.get(Lead, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_at = datetime.utcnow()

    session.add(record)
    session.commit()
    session.refresh(record)
    return record
