# Custom Pipeline Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let admins save a custom automated-test pipeline as a reusable scenario and later render it with any target/dataset.

**Architecture:** Persist custom scenario templates in a new database table and expose them through the existing scenarios API. The frontend builds a target/dataset-independent template from custom-mode state and posts it to the new endpoint.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Alembic, Pydantic, React, TypeScript, React Query, Vitest.

---

### Task 1: Backend Custom Scenario API

**Files:**
- Modify: `airedteam/storage/models.py`
- Create: `airedteam/services/custom_scenarios.py`
- Modify: `airedteam/api/deps.py`
- Modify: `airedteam/api/routers/scenarios.py`
- Create: `alembic/versions/0011_custom_scenarios.py`
- Test: `tests/integration/test_api_custom_scenarios.py`

- [ ] **Step 1: Write failing API integration test**

Create `tests/integration/test_api_custom_scenarios.py` with a test that posts a custom scenario containing `executors`, `scorers`, `sampling`, and `timeout_seconds`, then verifies `GET /api/scenarios` includes `custom:<id>` and `POST /api/scenarios/custom:<id>/runspec` injects a new target/dataset without storing the original ids.

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
uv run pytest tests/integration/test_api_custom_scenarios.py -q
```

Expected: fail because `POST /api/scenarios/custom` does not exist.

- [ ] **Step 3: Implement persistence and API**

Add `CustomScenario` ORM model, `CustomScenarioService`, dependency wiring, and scenario router support for listing, creation, and render.

- [ ] **Step 4: Add migration**

Add Alembic revision `0011_custom_scenarios.py` creating and dropping `custom_scenarios`.

- [ ] **Step 5: Run backend tests**

Run:

```bash
uv run pytest tests/integration/test_api_custom_scenarios.py tests/integration/test_api_plugins.py::test_list_plugins_and_scenarios tests/unit/test_alembic_migrations.py -q
```

Expected: all pass.

### Task 2: Frontend Save-As-Scenario Flow

**Files:**
- Create: `frontend/src/lib/customScenarioPayload.ts`
- Create: `frontend/tests/customScenarioPayload.test.ts`
- Modify: `frontend/src/pages/NewRun.tsx`
- Modify: `frontend/src/lib/i18n.tsx`

- [ ] **Step 1: Write failing frontend helper test**

Create `frontend/tests/customScenarioPayload.test.ts` covering that target/dataset ids are excluded and pipeline refs, scorer, sampling, and timeout are preserved.

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
cd frontend && npm test -- customScenarioPayload.test.ts --runInBand
```

Expected: fail because `customScenarioPayload` does not exist.

- [ ] **Step 3: Implement helper**

Create `buildCustomScenarioPayload` in `frontend/src/lib/customScenarioPayload.ts`.

- [ ] **Step 4: Wire UI**

Add modal state and save mutation to `NewRun.tsx`. Add a `Save as scenario` button in custom mode's Pipeline header. On success, invalidate `scenarios`, switch to preset mode, and select the returned scenario id.

- [ ] **Step 5: Add translations**

Add Chinese translations for the new labels and messages in `frontend/src/lib/i18n.tsx`.

- [ ] **Step 6: Run frontend tests/build**

Run:

```bash
cd frontend && npm test -- customScenarioPayload.test.ts --runInBand
cd frontend && npm run build
```

Expected: test and build pass.

### Task 3: Final Verification

**Files:**
- All changed files.

- [ ] **Step 1: Run full backend tests**

Run:

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend tests/build**

Run:

```bash
cd frontend && npm test -- --runInBand
cd frontend && npm run build
```

Expected: all tests and build pass.

- [ ] **Step 3: Inspect diff and status**

Run:

```bash
git status --short
git diff --stat
```

Expected: only custom scenario feature files are changed.
