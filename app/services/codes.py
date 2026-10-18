from sqids import Sqids

RESERVED = {"api", "docs", "health", "openapi.json", "redoc", "ui"}

_sqids = Sqids(min_length=7)


def encode_id(n: int) -> str:
    return _sqids.encode([n])
