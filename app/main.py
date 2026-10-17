from fastapi import FastAPI

from app.db import Base, engine
from app.models import link
from app.routers import links, redirect, ui

Base.metadata.create_all(engine)
app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(links.router)
app.include_router(ui.router)
app.include_router(redirect.router)
