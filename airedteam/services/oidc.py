from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth
from sqlalchemy import delete, update
from starlette.requests import Request
from starlette.responses import RedirectResponse

from airedteam.api.auth import AuthIdentity
from airedteam.config import Settings
from airedteam.storage.models import OIDCLoginTicket


class OIDCLoginError(RuntimeError):
    pass


def safe_next_path(value: str | None) -> str:
    if (
        not value
        or not value.startswith("/")
        or value.startswith("//")
        or "\\" in value
        or any(ord(character) < 32 for character in value)
    ):
        return "/dashboard"
    return value[:500]


def _ticket_hash(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def _text(value, *, limit: int) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result[:limit] if result else None


class OIDCService:
    def __init__(self, session_factory, settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.oauth = OAuth()
        if settings.oidc_enabled:
            endpoint = settings.oidc_endpoint.rstrip("/")
            self.oauth.register(
                name="airedteam_oidc",
                client_id=settings.oidc_client_id,
                client_secret=settings.oidc_client_secret.get_secret_value(),
                server_metadata_url=f"{endpoint}/.well-known/openid-configuration",
                client_kwargs={
                    "scope": "openid profile email",
                    "code_challenge_method": "S256",
                },
            )

    def _client(self):
        if not self.settings.oidc_enabled:
            raise OIDCLoginError("oidc_not_configured")
        return self.oauth.create_client("airedteam_oidc")

    async def start(self, request: Request, next_path: str | None) -> RedirectResponse:
        request.session["airedteam_oidc_next"] = safe_next_path(next_path)
        nonce = secrets.token_urlsafe(32)
        return await self._client().authorize_redirect(
            request,
            self.settings.oidc_callback_url,
            nonce=nonce,
        )

    async def complete(self, request: Request) -> tuple[str, str]:
        next_path = safe_next_path(request.session.pop("airedteam_oidc_next", None))
        try:
            token = await self._client().authorize_access_token(request)
        except Exception as exc:
            raise OIDCLoginError("provider_authentication_failed") from exc

        claims = dict(token.get("userinfo") or {})
        if not claims:
            raise OIDCLoginError("missing_id_token_claims")

        metadata = self._client().server_metadata
        if metadata.get("userinfo_endpoint"):
            try:
                userinfo = dict(await self._client().userinfo(token=token))
            except Exception:
                userinfo = {}
            if userinfo:
                if userinfo.get("sub") != claims.get("sub"):
                    raise OIDCLoginError("userinfo_subject_mismatch")
                claims.update(userinfo)

        identity = self._identity(claims, issuer=str(metadata.get("issuer") or self.settings.oidc_endpoint))
        ticket = await self._create_ticket(identity, next_path)
        return ticket, next_path

    def _identity(self, claims: dict, *, issuer: str) -> AuthIdentity:
        provider_subject = _text(claims.get("sub"), limit=500)
        if not provider_subject:
            raise OIDCLoginError("missing_subject")
        digest = hashlib.sha256(f"{issuer}\0{provider_subject}".encode()).hexdigest()
        email = _text(claims.get("email"), limit=320)
        display_name = (
            _text(claims.get("name"), limit=200)
            or _text(claims.get("preferred_username"), limit=200)
            or email
            or provider_subject[:200]
        )
        return AuthIdentity(
            subject=f"oidc:{digest}",
            display_name=display_name,
            email=email,
            picture=_text(claims.get("picture"), limit=2048),
            auth_method="oidc",
        )

    async def _create_ticket(self, identity: AuthIdentity, next_path: str) -> str:
        ticket = secrets.token_urlsafe(48)
        now = datetime.now(UTC).replace(tzinfo=None)
        async with self.session_factory() as session:
            await session.execute(delete(OIDCLoginTicket).where(OIDCLoginTicket.expires_at <= now))
            session.add(
                OIDCLoginTicket(
                    ticket_hash=_ticket_hash(ticket),
                    account_json=identity.public(),
                    next_path=next_path,
                    expires_at=now + timedelta(minutes=2),
                )
            )
            await session.commit()
        return ticket

    async def consume_ticket(self, ticket: str) -> tuple[AuthIdentity, str]:
        if not ticket or len(ticket) > 512:
            raise OIDCLoginError("invalid_ticket")
        now = datetime.now(UTC).replace(tzinfo=None)
        async with self.session_factory() as session:
            result = await session.execute(
                update(OIDCLoginTicket)
                .where(
                    OIDCLoginTicket.ticket_hash == _ticket_hash(ticket),
                    OIDCLoginTicket.consumed_at.is_(None),
                    OIDCLoginTicket.expires_at > now,
                )
                .values(consumed_at=now)
                .returning(OIDCLoginTicket.account_json, OIDCLoginTicket.next_path)
            )
            row = result.first()
            await session.commit()
        if row is None:
            raise OIDCLoginError("invalid_or_expired_ticket")
        account = row[0]
        return AuthIdentity(
            subject=account["subject"],
            display_name=account["display_name"],
            email=account.get("email"),
            picture=account.get("picture"),
            auth_method="oidc",
        ), safe_next_path(row[1])

    def frontend_login_url(self, **params: str) -> str:
        return f"{self.settings.frontend_url.rstrip('/')}/login?{urlencode(params)}"
