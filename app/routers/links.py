from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from app.cache import r
from app.db import get_db
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkOut, LinkUpdate
from app.services.codes import RESERVED, encode_id

router = APIRouter(prefix="/api/links", tags=["links"])

BASE_URL = "http://localhost:8000"


@router.post("", response_model=LinkOut, status_code=201)
def create_links(body: LinkCreate, db: Session = Depends(get_db)):
    if body.alias and body.alias.lower() in RESERVED:
        raise HTTPException(400, "That alias is reserved")

    link = Link(
        code=body.alias or "tmp", original_url=str(body.url), expires_at=body.expires_at
    )
    db.add(link)
    try:
        db.flush()
        if not body.alias:
            link.code = encode_id(link.id)
            db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        if body.alias:
            raise HTTPException(409, "Alias is already taken")
        raise HTTPException(500, "Could not create link")
    return LinkOut(
        code=link.code,
        short_url=f"{BASE_URL}/{link.code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )


@router.patch("/{code}", response_model=LinkOut)
def update_link(code: str, payload: LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.code == code).first()
    if link is None:
        raise HTTPException(status_code=404, detail="Link Not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field == "url":
            link.original_url = str(value)
        else:
            setattr(link, field, value)

    db.commit()
    r.delete(f"link:{code}")
    db.refresh(link)

    return LinkOut(
        code=link.code,
        short_url=f"{BASE_URL}/{link.code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )


@router.delete("/{code}", status_code=204)
def delete_link(code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.code == code).first()

    if link is None:
        raise HTTPException(status_code=404, detail="Link Not found")

    db.delete(link)
    db.commit()
    r.delete(f"link:{code}")
