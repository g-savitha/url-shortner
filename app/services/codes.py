import secrets
import string

ALPHABET = string.ascii_letters + string.digits
RESERVED = {"api", "docs", "health", "openapi.json", "redoc", "ui"}


def generate_code(length: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
