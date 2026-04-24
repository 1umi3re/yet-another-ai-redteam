from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from airedteam.api.deps import AppState, get_state, require_admin

router = APIRouter()


class CreateRunIn(BaseModel):
    name: str
    target_id: str


class CreateConversationIn(BaseModel):
    seed_attempt_id: str | None = None


class TurnIn(BaseModel):
    text: str


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


@router.post("/manual/runs/{rid}/conversations/{aid}/turn")
async def append_turn(rid: str, aid: str, body: TurnIn,
                      _=Depends(require_admin),
                      state: AppState = Depends(get_state)):
    try:
        messages = await state.manual.append_turn(rid, aid, body.text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"conversation": messages, "last_assistant_text": messages[-1]["text"]}


@router.post("/manual/runs/{rid}/finish")
async def finish(rid: str, _=Depends(require_admin),
                 state: AppState = Depends(get_state)):
    await state.manual.finish(rid)
    return {"ok": True}
