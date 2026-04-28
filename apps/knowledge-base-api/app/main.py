from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, select


class RecordStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class Article(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    name: str = SQLField(index=True, min_length=2, max_length=120)
    description: str | None = SQLField(default=None, max_length=500)
    owner: str | None = SQLField(default=None, max_length=80)
    status: RecordStatus = SQLField(default=RecordStatus.draft)
    created_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class ArticleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner: str | None = Field(default=None, max_length=80)
    status: RecordStatus = Field(default=RecordStatus.draft)


class ArticleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner: str | None = Field(default=None, max_length=80)
    status: RecordStatus | None = None


class ArticleRead(BaseModel):
    id: int
    name: str
    description: str | None
    owner: str | None
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


engine = create_engine("sqlite:///data/app.db", connect_args={"check_same_thread": False})
app = FastAPI(title="Knowledge Base API", version="1.0.0")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def verify_token(x_api_token: str | None = Header(default=None, alias="X-API-Token")) -> None:
    # 生产环境请改为读取安全配置中心，并增加细粒度权限控制。
    if x_api_token not in (None, "dev-token"):
        raise HTTPException(status_code=401, detail="Invalid API token")


@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/articles", response_model=ArticleRead, dependencies=[Depends(verify_token)])
def create_record(payload: ArticleCreate, session: Session = Depends(get_session)) -> Article:
    record = Article(**payload.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@app.get("/api/v1/articles", response_model=list[ArticleRead], dependencies=[Depends(verify_token)])
def list_records(
    status: RecordStatus | None = Query(default=None),
    owner: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Article]:
    stmt = select(Article)
    if status:
        stmt = stmt.where(Article.status == status)
    if owner:
        stmt = stmt.where(Article.owner == owner)
    stmt = stmt.order_by(Article.created_at.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@app.get("/api/v1/articles/{record_id}", response_model=ArticleRead, dependencies=[Depends(verify_token)])
def get_record(record_id: int, session: Session = Depends(get_session)) -> Article:
    record = session.get(Article, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.patch("/api/v1/articles/{record_id}", response_model=ArticleRead, dependencies=[Depends(verify_token)])
def update_record(
    record_id: int,
    payload: ArticleUpdate,
    session: Session = Depends(get_session),
) -> Article:
    record = session.get(Article, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_at = datetime.utcnow()

    session.add(record)
    session.commit()
    session.refresh(record)
    return record
