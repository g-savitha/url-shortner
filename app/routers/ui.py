import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

router = APIRouter(tags=["ui"])

INDEX = Path(__file__).resolve().parents[1] / "static" / "index.html"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@router.get("/")
def playground():
    return FileResponse(INDEX)


@router.get("/ui/probe/{code}")
def probe(code: str, request: Request):
    url = str(request.base_url) + code
    opener = urllib.request.build_opener(_NoRedirect)
    started = time.perf_counter()
    try:
        with opener.open(url, timeout=5) as resp:
            status = resp.status
            headers = resp.headers
    except urllib.error.HTTPError as e:
        status = e.code
        headers = e.headers
    ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "status": status,
        "x_cache": headers.get("X-Cache"),
        "location": headers.get("Location"),
        "ms": ms,
    }
