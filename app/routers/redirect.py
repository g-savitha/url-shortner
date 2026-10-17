import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import update

from app.cache import TTL_SECONDS, r
from app.db import get_db
from app.models.link import Link

router = APIRouter(tags=["redirect"])


@router.get("/{code}")
def follow(code: str, db: Session = Depends(get_db)):
    key = f"link:{code}"
    cached = r.get(key)

    if cached:
        data = json.loads(cached)
    else:
        link = db.scalar(select(Link).where(Link.code == code))
        if link is None or link.status != "active":
            raise HTTPException(404, "Link not found")
        data = {
            "id": link.id,
            "url": link.original_url,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        }
        r.set(key, json.dumps(data), ex=TTL_SECONDS)

    if data["expires_at"] and datetime.fromisoformat(data["expires_at"]) < datetime.now(
        timezone.utc
    ):
        raise HTTPException(410, "Link Expired")

    db.execute(
        update(Link)
        .where(Link.id == data["id"])
        .values(click_count=Link.click_count + 1)
    )
    db.commit()

    resp = RedirectResponse(data["url"], status_code=302)
    resp.headers["X-Cache"] = "HIT" if cached else "MISS"

    return resp
