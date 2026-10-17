from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import update

from app.db import get_db
from app.models.link import Link

router = APIRouter(tags=["redirect"])


@router.get("/{code}")
def follow(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None or link.status != "active":
        raise HTTPException(404, "Link not found")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Link Expired")

    db.execute(
        update(Link).where(Link.id == link.id).values(click_count=Link.click_count + 1)
    )
    db.commit()

    return RedirectResponse(link.original_url, status_code=302)
