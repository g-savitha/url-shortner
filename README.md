# url-shortner

A URL shortener built from scratch with **FastAPI**, **PostgreSQL** and **Redis**. It's a learning project for backend and system design fundamentals: short-code generation, redirects, expiry, click counting and (next) caching.

## What it does

- Create a short link from a long URL, with an optional custom alias and expiry time
- Visit `/{code}` to get redirected to the original URL (`302`)
- Expired links return `410 Gone`; unknown or disabled links return `404`
- Every redirect increments the link's click count

## Tech stack

| Part          | Tool                                             |
| ------------- | ------------------------------------------------ |
| Web framework | FastAPI (served by uvicorn)                      |
| Database      | PostgreSQL 17                                    |
| ORM / driver  | SQLAlchemy 2 + psycopg 3                         |
| Settings      | pydantic-settings (reads `.env`)                 |
| Cache         | Redis 7 (container running, caching in progress) |
| Packages      | uv                                               |
| Local infra   | Docker Compose                                   |

## Getting started

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker Desktop.

```bash
git clone https://github.com/g-savitha/url-shortner.git
cd url-shortner
cp .env.example .env    # then fill in the values (see below)
uv sync                 # install dependencies into .venv
make db                 # start Postgres and Redis
make dev                # start the API at http://localhost:8000
```

Interactive API docs: http://localhost:8000/docs

## Playground UI

Open http://localhost:8000 for a minimal dark UI to create links, edit/delete them (session list in `localStorage`), and test redirects via `GET /ui/probe/{code}` (returns status, `X-Cache`, `Location`, and latency — browser `fetch` with `redirect: 'manual'` hides these).

## Make commands

| Command             | What it does                       |
| ------------------- | ---------------------------------- |
| `make dev`          | Run the API with auto-reload       |
| `make db`           | Start Postgres and Redis in Docker |
| `make psql`         | Open a Postgres shell              |
| `make desc t=links` | Describe a table                   |

## API

| Method | Path         | Description                  | Responses                                                           |
| ------ | ------------ | ---------------------------- | ------------------------------------------------------------------- |
| `GET`  | `/health`    | Health check                 | `200`                                                               |
| `POST` | `/api/links` | Create a short link          | `201`, `400` reserved alias, `409` alias taken, `422` invalid input |
| `GET`  | `/{code}`    | Redirect to the original URL | `302`, `404`, `410`                                                 |

Create a link:

```bash
curl -X POST http://localhost:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://gsavitha.in/blog/blog-audio-player/", "alias": "audio"}'
```

```json
{
  "code": "audio",
  "short_url": "http://localhost:8000/audio",
  "original_url": "https://gsavitha.in/blog/blog-audio-player/",
  "expires_at": null
}
```

Request body fields:

- `url` (required): must be a valid `http` or `https` URL
- `alias` (optional): 3 to 16 characters from `A-Z a-z 0-9 _ -`; reserved words like `api`, `docs`, `health` are rejected
- `expires_at` (optional): ISO 8601 timestamp; after it, the link returns `410`

## Data model

```sql
links (
  id           BIGINT PRIMARY KEY,
  code         VARCHAR(16) UNIQUE NOT NULL,
  original_url TEXT NOT NULL,
  status       VARCHAR(10) DEFAULT 'active',
  click_count  BIGINT DEFAULT 0,
  expires_at   TIMESTAMPTZ NULL,
  created_at   TIMESTAMPTZ DEFAULT now()
)
```

## Design decisions

- **Random 7-character base62 codes** via Python's `secrets` module, so codes can't be guessed. 62^7 is about 3.5 trillion combinations, so collisions are rare.
- **The database enforces uniqueness.** `code` is `UNIQUE`; on a collision we roll back and retry (up to 5 times). This stays correct even when two requests race.
- **302, not 301.** Browsers cache 301s and skip the server, which would hide repeat clicks. 302 keeps every click countable.
- **Atomic click counter.** `click_count = click_count + 1` runs inside Postgres, so concurrent clicks never overwrite each other.
- **Redirects at the root, API under `/api`.** Short links stay short, and API routes can get their own auth and rate limits later.
- **Route order matters.** `/{code}` matches almost anything, so it's registered after `/health` and `/api/links`.

## Project structure

```
app/
├── main.py           # creates the app, registers routers
├── config.py         # settings from .env
├── db.py             # engine, session, Base, get_db dependency
├── models/link.py    # SQLAlchemy Link table
├── schemas/link.py   # Pydantic request/response models
├── routers/
│   ├── links.py      # POST /api/links
│   ├── ui.py         # GET / playground, GET /ui/probe/{code}
│   └── redirect.py   # GET /{code}
├── static/index.html # playground UI
└── services/codes.py # code generation, reserved words
```

## Roadmap

- [x] Create links with alias and expiry
- [x] 302 redirect with click counting
- [ ] Redis cache-aside for redirects
- [ ] Move click counting to Redis and flush to Postgres in batches
- [ ] `GET /api/links/{code}/stats` and `DELETE /api/links/{code}`
- [ ] Rate limiting on link creation
- [ ] Tests with pytest
- [ ] Alembic migrations instead of `create_all`
- [ ] Deploy on a custom domain (savii.in)
