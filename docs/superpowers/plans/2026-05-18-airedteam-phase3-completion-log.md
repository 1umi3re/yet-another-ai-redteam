# AiRedTeam Phase 3 Completion Log

**Date:** 2026-05-18

**Goal:** Improve the manual-console workflow and make prompt/evaluator behavior auditable enough for repeatable benchmark work.

Phase 3 shipped as five small commits:

- `dd23bf0 feat(prompt-assets): add prompt overrides and snapshots`
- `e4c70f6 feat(manual): add resume, converters, dataset prompts, evaluators`
- `e9e8ebf feat(targets): check streaming and increase timeouts`
- `5d1e86f feat(datasets): add full advbench and harmbench fixtures`
- `01025b2 chore(gitignore): ignore superpowers workspace`

## What Shipped

### Prompt Assets

Prompt templates for evaluators and attack executors are now managed as first-class assets.

- Built-in prompt assets live in `airedteam/builtins/prompt_assets/assets.json`.
- Overrides are persisted in `prompt_asset_overrides`.
- Active overrides can replace built-ins without changing executor/scorer code.
- Rendered prompt snapshots are written to blob storage for attempts and scores.
- Snapshot paths are stored on `Attempt.prompt_snapshot_blob_path` and `Score.prompt_snapshot_blob_path`.
- APIs expose asset listing, override creation/update, activation, and snapshot retrieval.
- Frontend includes a Prompt Assets page for inspecting built-ins and managing overrides.

Primary files:

- `airedteam/services/prompt_assets.py`
- `airedteam/api/routers/prompt_assets.py`
- `airedteam/builtins/prompt_assets/assets.json`
- `alembic/versions/0003_phase3_prompt_assets.py`
- `frontend/src/pages/PromptAssets.tsx`
- `frontend/src/components/PluginParamsForm.tsx`

Integrated plugins:

- `llm_judge`
- `crescendo`
- `pair`

### Manual Console

The manual console now supports longer-running human sessions instead of one-off chats.

- Manual runs can be ended explicitly with an End run button.
- Running manual sessions can be resumed from the Manual Console or Runs page.
- Runs display the target being tested.
- The side panel is now named Session tools and split into:
  - Benchmark prompt
  - Converters
  - Evaluator
- Benchmark prompts can be loaded from seeded/uploaded datasets.
- Converter chains can be selected, previewed, applied, and sent with the user turn.
- Each transformed turn stores metadata with original input, transformed input, converter chain, and converter params.
- Conversations can be scored from the manual console with a selected evaluator.
- Manual session state reports whether the current conversation has scores.

Primary files:

- `airedteam/services/manual.py`
- `airedteam/services/converters.py`
- `airedteam/api/routers/manual.py`
- `airedteam/api/routers/converters.py`
- `airedteam/api/routers/datasets.py`
- `frontend/src/pages/ManualConsole.tsx`
- `frontend/src/pages/Runs.tsx`

### Target Connectivity Checks

Target checking now better reflects production benchmark behavior.

- OpenAI-compatible target timeout default increased to 300 seconds.
- HTTP connect timeout is bounded separately at 30 seconds.
- Connectivity check timeout increased to 180 seconds.
- OpenAI-compatible target checks whether streaming chat completions work by sending `stream: true`.
- Target check API and UI surface `stream_ok` and `stream_error`.

Primary files:

- `airedteam/builtins/targets/openai_compat.py`
- `airedteam/api/routers/targets.py`
- `frontend/src/pages/Targets.tsx`

### Full Benchmark Fixtures

The bundled benchmark data now includes full JSON fixtures instead of only small samples.

- AdvBench full fixture: 520 items.
- HarmBench full fixture: 400 items.
- `airedteam seed-datasets` now seeds full fixtures by default.
- `airedteam seed-datasets --sample` keeps the old smoke-test behavior.
- Full JSON fixtures are packaged in the wheel.
- Raw source files are intentionally not committed.

Primary files:

- `airedteam/builtins/datasets/samples/advbench_full.json`
- `airedteam/builtins/datasets/samples/harmbench_full.json`
- `airedteam/cli.py`
- `pyproject.toml`
- `README.md`

## API Additions

- `GET /api/prompt-assets`
- `GET /api/prompt-assets/{asset_id}`
- `POST /api/prompt-assets/{asset_id}/overrides`
- `PATCH /api/prompt-assets/overrides/{override_id}`
- `POST /api/prompt-assets/{asset_id}/active-override`
- `GET /api/runs/{rid}/attempts/{aid}/prompt-snapshot`
- `GET /api/runs/{rid}/scores/{sid}/prompt-snapshot`
- `POST /api/converters/preview`
- `GET /api/datasets/{dataset_id}/items`
- `GET /api/manual/runs/{rid}/session`
- `POST /api/manual/runs/{rid}/conversations/{aid}/evaluate`

## Verification

Phase 3 added or updated tests around:

- prompt asset service behavior
- prompt asset API behavior
- prompt asset plugin integration
- manual console API behavior
- converter preview API
- dataset item listing API
- target streaming checks
- full dataset fixture shape
- prompt snapshots in run service and multi-turn executors

Recent verification performed during Phase 3:

- `uv run pytest -q` passed after manual evaluator work.
- `uv run pytest -q` passed after full dataset fixture work.
- `npx tsc --noEmit` passed after the manual console side-panel split.

## Known Follow-Ups

- Add a richer prompt asset diff/preview workflow before activating overrides.
- Add pagination/search to `GET /api/datasets/{dataset_id}/items`; current endpoint is limited to 500 items.
- Add evaluator result comparison in the manual console when the same conversation has multiple scores.
- Add cancellation or timeout controls for manual evaluator calls.
- Consider a dedicated run detail view for prompt snapshots instead of exposing only raw JSON.
