from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl
    alias: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{8,16}$")
    expires_at: datetime | None = None


class LinkOut(BaseModel):
    code: str
    short_url: str
    original_url: str
    expires_at: datetime | None


class LinkUpdate(BaseModel):
    url: HttpUrl | None = None
    expires_at: datetime | None = None
