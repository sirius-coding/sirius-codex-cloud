from fastapi import Depends, FastAPI, Header, HTTPException

from .config import settings
from .db import Base, engine
from .routes.business import router as business_router
from .routes.health import router as health_router

app = FastAPI(title="程序员私活项目模板", version="1.0.0")


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


def verify_token(authorization: str | None = Header(default=None)):
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


app.include_router(health_router)
app.include_router(business_router, dependencies=[Depends(verify_token)])


@app.get("/")
def index():
    return {
        "name": settings.app_name,
        "env": settings.env,
        "message": "Freelance project template is running",
        "docs": "/docs",
    }
