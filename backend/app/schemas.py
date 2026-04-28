from datetime import date

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contact: str = ""
    notes: str = ""


class ClientRead(ClientCreate):
    id: int

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    client_id: int
    title: str = Field(min_length=1, max_length=200)
    status: str = "todo"
    budget: float = 0
    deadline: date | None = None


class ProjectRead(ProjectCreate):
    id: int

    class Config:
        from_attributes = True
