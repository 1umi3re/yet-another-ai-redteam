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
AIREDTEAM_JWT_TTL_MINUTES=10080 # optional, token lifetime (default 7d)
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

## Seeding datasets (AdvBench / HarmBench)

Bundled JSON versions of **AdvBench** (520 prompts) and **HarmBench** (400 prompts) are shipped with the package. Seed them into your running instance with:

```bash
airedteam seed-datasets
```

This registers both as `json_upload` datasets using the same env/DB your API uses (set `AIREDTEAM_MASTER_KEY`, `AIREDTEAM_DATABASE_URL`, `AIREDTEAM_BLOB_DIR` first). They then appear in the `/datasets` page of the UI and can be selected in **New run**.

Inside Docker compose:

```bash
docker compose exec api airedteam seed-datasets
```

For quick smoke tests, seed the smaller curated samples instead:

```bash
airedteam seed-datasets --sample
```

---

## Phase 2 — Deeper Attacks & Human-in-the-Loop

### Multi-turn executors

Beyond single-turn prompts, **airedteam** now supports multi-turn executors that engage targets in multi-step conversations to elicit policy violations:

- **Crescendo** — Incrementally escalates prompts across turns, using an attacker LLM to generate follow-up messages when the target refuses. Configure via `executor.plugin = "crescendo"` with params `attacker_config_id`, `goal`, and `max_turns`.
- **PAIR** — Prompt Automatic Iterative Refinement. Uses an attacker to iteratively refine prompts based on target responses. Configure via `executor.plugin = "pair"` with params `attacker_config_id`, `judge_config_id`, `goal`, and `max_turns`.

Both store full conversation history in blob storage (`conversation_blob_path` on each `Attempt`). To implement custom multi-turn strategies, extend `airedteam.builtins.executors.multi_turn_base.MultiTurnExecutor` — see that module for the extension API.

### New converters

Phase 2 adds five prompt transformation converters:

- **unicode_obfuscation** — Replaces ASCII characters with Unicode lookalikes (e.g., `a` → `а` Cyrillic).
- **leetspeak** — Substitutes letters with numbers/symbols (e.g., `elite` → `31337`).
- **persona_role_play_prefix** — Wraps prompts in a persona instruction ("You are a helpful assistant who...").
- **emoji_substitution** — Replaces words with emoji (e.g., `fire` → `🔥`).
- **translation_llm** — Translates prompts to another language via an LLM before sending them to the target. Requires a `translator_config_id` param pointing to a translation-capable target.

All available via the "Converters" tab when creating a run in the UI.

### Manual console

Navigate to `/manual` in the UI to interactively chat with any registered target. Pick a target, start a conversation, and send messages turn-by-turn. Useful for:

- Exploratory testing of new targets or prompts.
- Reproducing edge cases found in automated runs.
- Operator-driven attacks that require adaptive reasoning.

Any automated attempt in a run can be **replayed** into a manual session via the attempt drawer's **"Replay in Manual Console"** button, seeding the conversation history so you can continue from where the executor left off.

### Reviewer annotation

Automated scorers (refusal, regex, substring, LLM judge) produce initial verdicts, but operators often need to override incorrect labels. When viewing an attempt in the UI:

1. Open the attempt drawer (click any row in the attempts table).
2. Locate the scores section.
3. Click "Override" next to a score to set `reviewer_label` (true/false) and `reviewer_notes`.
4. Annotations persist to the database (`scores.reviewer_label`, `reviewer_notes`, `reviewer_id`, `reviewed_at`).
5. Export or query runs to incorporate human-verified ground truth into your eval metrics.

The annotation API is `PATCH /api/runs/{rid}/scores/{sid}` with JSON body `{"reviewer_label": <bool>, "reviewer_notes": "<string>"}`.

### Configuration unchanged

Phase 2 features do not introduce new environment variables. The same three secrets from Phase 1 remain required:

- `AIREDTEAM_MASTER_KEY` — Fernet key for encrypting target secrets.
- `AIREDTEAM_ADMIN_PASSWORD` — Login password for the web UI.
- `AIREDTEAM_JWT_SECRET` — HMAC secret for signing JWTs (optional but recommended).
