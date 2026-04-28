import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import Base, check_db_connection, engine
from .routes.business import router as business_router
from .routes.health import router as health_router

settings = get_settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    check_db_connection()
    yield


app = FastAPI(title="程序员私活项目模板", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


app.include_router(health_router)
app.include_router(business_router, prefix=settings.api_prefix, dependencies=[Depends(verify_token)])


@app.get("/")
def index():
    return {
        "name": settings.app_name,
        "env": settings.env,
        "message": "Freelance project template is running",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }
