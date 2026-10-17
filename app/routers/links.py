from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session

from app.db import get_db
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkOut
from app.services.codes import RESERVED, generate_code

router = APIRouter(prefix="/api/links", tags=["links"])

BASE_URL = "http://localhost:8000"


@router.post("", response_model=LinkOut, status_code=201)
def create_links(body: LinkCreate, db: Session = Depends(get_db)):
    if body.alias and body.alias.lower() in RESERVED:
        raise HTTPException(400, "That alias is reserved")

    for _ in range(5):
        code = body.alias or generate_code()
        link = Link(code=code, original_url=str(body.url), expires_at=body.expires_at)
        db.add(link)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if body.alias:
                raise HTTPException(409, "Alias is already taken")
    else:
        raise HTTPException(500, "Could not generate a unique code")
    return LinkOut(
        code=link.code,
        short_url=f"{BASE_URL}/{link.code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )
