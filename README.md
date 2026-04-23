# airedteam

Low-code AI redteam testing framework. Backend: FastAPI + asyncio. Frontend: React + Vite.

## Local quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # set AIREDTEAM_MASTER_KEY
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
