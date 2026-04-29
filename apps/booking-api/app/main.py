from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
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
        app_name=os.getenv("APP_NAME", "Booking API"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        api_token=os.getenv("API_TOKEN", "dev-token"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/booking.db"),
    )


settings = get_settings()


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Booking(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    client_name: str
    service_name: str
    start_at: datetime
    end_at: datetime
    notes: str | None = None
    status: BookingStatus = SQLField(default=BookingStatus.pending)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class BookingCreate(BaseModel):
    client_name: str = Field(min_length=2, max_length=50)
    service_name: str = Field(min_length=2, max_length=80)
    start_at: datetime
    end_at: datetime
    notes: str | None = Field(default=None, max_length=300)

    @field_validator("end_at")
    @classmethod
    def validate_end_at(cls, value: datetime, info):
        start_at = info.data.get("start_at")
        if start_at and value <= start_at:
            raise ValueError("end_at 必须晚于 start_at")
        return value


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    service_name: str
    start_at: datetime
    end_at: datetime
    notes: str | None
    status: BookingStatus


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


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
def startup() -> None:
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


@app.post(f"{settings.api_prefix}/bookings", response_model=BookingRead, dependencies=[Depends(verify_token)])
def create_booking(payload: BookingCreate, session: Session = Depends(get_session)) -> Booking:
    overlap_stmt = select(Booking).where(
        Booking.start_at < payload.end_at,
        Booking.end_at > payload.start_at,
        Booking.status != BookingStatus.cancelled,
    )
    overlap = session.exec(overlap_stmt).first()
    if overlap:
        raise HTTPException(status_code=409, detail="时间段冲突，已有预约")

    booking = Booking(**payload.model_dump())
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@app.get(f"{settings.api_prefix}/bookings", response_model=list[BookingRead], dependencies=[Depends(verify_token)])
def list_bookings(
    day: datetime | None = Query(default=None, description="按某天过滤"),
    status: BookingStatus | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[Booking]:
    stmt = select(Booking)
    if day:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(Booking.start_at >= day_start, Booking.start_at < day_end)
    if status:
        stmt = stmt.where(Booking.status == status)
    stmt = stmt.order_by(Booking.start_at)
    return list(session.exec(stmt).all())


@app.patch(f"{settings.api_prefix}/bookings/{{booking_id}}/status", response_model=BookingRead, dependencies=[Depends(verify_token)])
def update_booking_status(booking_id: int, payload: BookingStatusUpdate, session: Session = Depends(get_session)) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    booking.status = payload.status
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
