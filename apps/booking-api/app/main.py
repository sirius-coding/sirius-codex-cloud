from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField, Session, SQLModel, create_engine, select


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
    id: int
    client_name: str
    service_name: str
    start_at: datetime
    end_at: datetime
    notes: str | None
    status: BookingStatus


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


engine = create_engine("sqlite:///data/booking.db", connect_args={"check_same_thread": False})
app = FastAPI(title="Booking API", version="1.0.0")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def startup() -> None:
    SQLModel.metadata.create_all(engine)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/bookings", response_model=BookingRead)
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


@app.get("/api/v1/bookings", response_model=list[BookingRead])
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


@app.patch("/api/v1/bookings/{booking_id}/status", response_model=BookingRead)
def update_booking_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    session: Session = Depends(get_session),
) -> Booking:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="预约不存在")

    booking.status = payload.status
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
