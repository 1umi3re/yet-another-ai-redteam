from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from airedteam.api.deps import AppState, get_state, require_admin

router = APIRouter()


class CreateRunIn(BaseModel):
    name: str
    target_id: str


class CreateConversationIn(BaseModel):
    seed_attempt_id: str | None = None


class TurnIn(BaseModel):
    text: str
    converters: list[dict[str, Any]] = Field(default_factory=list)


class EvaluateIn(BaseModel):
    plugin: str
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/manual/runs")
async def create_run(body: CreateRunIn, _=Depends(require_admin),
                     state: AppState = Depends(get_state)):
    rid = await state.manual.create_run(name=body.name, target_id=body.target_id)
    return {"run_id": rid}


@router.post("/manual/runs/{rid}/conversations")
async def create_conversation(rid: str, body: CreateConversationIn,
                              _=Depends(require_admin),
                              state: AppState = Depends(get_state)):
    try:
        attempt_id, messages = await state.manual.create_conversation(
            rid, seed_attempt_id=body.seed_attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"attempt_id": attempt_id, "conversation": messages}


@router.get("/manual/runs/{rid}/session")
async def get_session(rid: str, _=Depends(require_admin),
                      state: AppState = Depends(get_state)):
    try:
        return await state.manual.get_session(rid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/manual/runs/{rid}/conversations/{aid}/turn")
async def append_turn(rid: str, aid: str, body: TurnIn,
                      _=Depends(require_admin),
                      state: AppState = Depends(get_state)):
    try:
        messages = await state.manual.append_turn(rid, aid, body.text, body.converters)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"conversation": messages, "last_assistant_text": messages[-1]["text"]}


@router.post("/manual/runs/{rid}/conversations/{aid}/evaluate")
async def evaluate_conversation(rid: str, aid: str, body: EvaluateIn,
                                _=Depends(require_admin),
                                state: AppState = Depends(get_state)):
    try:
        score = await state.manual.evaluate_attempt(
            rid,
            aid,
            {"plugin": body.plugin, "params": body.params},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"evaluated": True, "score": score, "scores": await state.manual.scores_for_attempt(aid)}


@router.post("/manual/runs/{rid}/finish")
async def finish(rid: str, _=Depends(require_admin),
                 state: AppState = Depends(get_state)):
    await state.manual.finish(rid)
    return {"ok": True}
