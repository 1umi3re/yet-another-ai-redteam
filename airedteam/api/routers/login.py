from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from airedteam.api.auth import issue_token
from airedteam.api.deps import AppState, get_state

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, state: AppState = Depends(get_state)) -> LoginResponse:
    if req.password != state.settings.admin_password:
        raise HTTPException(401, "invalid password")
    return LoginResponse(
        token=issue_token(
            secret=state.settings.jwt_secret, admin_id="admin", ttl_minutes=state.settings.jwt_ttl_minutes
        )
    )
