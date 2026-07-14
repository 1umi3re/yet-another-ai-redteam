from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from airedteam.api.auth import AuthIdentity, issue_token
from airedteam.api.deps import AppState, get_state, require_identity
from airedteam.services.oidc import OIDCLoginError

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class TicketExchangeRequest(BaseModel):
    ticket: str


class AccountResponse(BaseModel):
    subject: str
    display_name: str
    email: str | None = None
    picture: str | None = None
    auth_method: str

    @classmethod
    def from_identity(cls, identity: AuthIdentity) -> "AccountResponse":
        return cls(**identity.public())


class LoginResponse(BaseModel):
    token: str
    account: AccountResponse
    next: str = "/dashboard"


class AuthConfigResponse(BaseModel):
    oidc_enabled: bool
    oidc_forced: bool
    password_enabled: bool
    oidc_start_url: str | None = None


def _login_response(state: AppState, identity: AuthIdentity, *, next_path: str = "/dashboard") -> LoginResponse:
    return LoginResponse(
        token=issue_token(
            secret=state.settings.jwt_secret,
            admin_id=identity.subject,
            ttl_minutes=state.settings.jwt_ttl_minutes,
            identity=identity,
        ),
        account=AccountResponse.from_identity(identity),
        next=next_path,
    )


@router.get("/auth/config", response_model=AuthConfigResponse)
async def auth_config(state: AppState = Depends(get_state)) -> AuthConfigResponse:
    enabled = state.settings.oidc_enabled
    return AuthConfigResponse(
        oidc_enabled=enabled,
        oidc_forced=state.settings.oidc_force_auth,
        password_enabled=not state.settings.oidc_force_auth,
        oidc_start_url="/api/auth/oidc/start" if enabled else None,
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, state: AppState = Depends(get_state)) -> LoginResponse:
    if state.settings.oidc_force_auth:
        raise HTTPException(403, "password login is disabled; use OIDC")
    if req.password != state.settings.admin_password:
        raise HTTPException(401, "invalid password")
    identity = AuthIdentity(subject="admin", display_name="Administrator", auth_method="password")
    return _login_response(state, identity)


@router.get("/auth/oidc/start")
async def oidc_start(
    request: Request,
    next: str | None = None,
    state: AppState = Depends(get_state),
):
    if not state.settings.oidc_enabled:
        raise HTTPException(404, "OIDC is not configured")
    try:
        return await state.oidc.start(request, next)
    except Exception:
        raise HTTPException(503, "OIDC is unavailable") from None


@router.get("/auth/oidc/callback")
async def oidc_callback(request: Request, state: AppState = Depends(get_state)) -> RedirectResponse:
    if not state.settings.oidc_enabled:
        raise HTTPException(404, "OIDC is not configured")
    try:
        ticket, next_path = await state.oidc.complete(request)
        return RedirectResponse(
            state.oidc.frontend_login_url(oidc_ticket=ticket, next=next_path),
            status_code=303,
        )
    except Exception:
        request.session.pop("airedteam_oidc_next", None)
        return RedirectResponse(
            state.oidc.frontend_login_url(oidc_error="authentication_failed"),
            status_code=303,
        )


@router.post("/auth/oidc/exchange", response_model=LoginResponse)
async def oidc_exchange(req: TicketExchangeRequest, state: AppState = Depends(get_state)) -> LoginResponse:
    if not state.settings.oidc_enabled:
        raise HTTPException(404, "OIDC is not configured")
    try:
        identity, next_path = await state.oidc.consume_ticket(req.ticket)
    except OIDCLoginError:
        raise HTTPException(401, "invalid or expired OIDC login") from None
    return _login_response(state, identity, next_path=next_path)


@router.get("/auth/me", response_model=AccountResponse)
async def me(identity: AuthIdentity = Depends(require_identity)) -> AccountResponse:
    return AccountResponse.from_identity(identity)
