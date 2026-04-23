# airedteam

Low-code AI redteam testing framework. Backend: FastAPI + asyncio. Frontend: React + Vite.

## Configuration

Three secrets must be set in `.env` before running (either locally or via Docker). Copy the template first:

```bash
cp .env.example .env
```

Then set the following values:

### `AIREDTEAM_MASTER_KEY` (required)

A Fernet key used to encrypt target secrets (API keys) at rest in the database. **Must be a url-safe base64-encoded 32-byte key** (44 characters).

Generate one:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into `.env`:

```
AIREDTEAM_MASTER_KEY=GxkU...=
```

⚠️ Rotating this key invalidates all previously stored target secrets — keep it safe and back it up.

### `AIREDTEAM_ADMIN_PASSWORD` (required)

The password used to log into the web UI / obtain a JWT via `POST /api/login`. Pick any strong string:

```
AIREDTEAM_ADMIN_PASSWORD=<your-strong-password>
```

### `AIREDTEAM_JWT_SECRET` (recommended)

HMAC secret used to sign the JWTs issued by `/api/login`. Defaults to `change-me-jwt` — **override it in any non-local deployment**. Any sufficiently long random string works:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```
AIREDTEAM_JWT_SECRET=<paste output>
AIREDTEAM_JWT_TTL_MINUTES=720   # optional, token lifetime (default 12h)
```

### Docker compose

`docker-compose.yml` reads `AIREDTEAM_MASTER_KEY`, `AIREDTEAM_ADMIN_PASSWORD`, and `AIREDTEAM_JWT_SECRET` from your shell (or a `.env` file in the project root — Compose loads it automatically). Verify with:

```bash
docker compose config | grep AIREDTEAM_
```

---

## Local quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
# .env already prepared per the Configuration section above
alembic upgrade head
airedteam serve
```

In another shell:

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 and log in with `AIREDTEAM_ADMIN_PASSWORD`.

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pytest -q
```
