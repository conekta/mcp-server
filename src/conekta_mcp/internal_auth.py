"""Internal mode: trusted Conekta services operate as a company without its private key.

A caller authenticates with ``Authorization: Bearer <service credential>`` and names
the company in ``X-Company-Id``. The server then calls payments-api through
``/internal/api/<public path>`` with an internal JWT and an encrypted
``X-Company-Context``, so the merchant's system key never leaves payments-api.

There is no feature flag: internal mode is active wherever its secrets are loaded.

- Neither secret set: every request with ``X-Company-Id`` gets a 401 and public
  mode (``Bearer key_xxx``) works as before.
- Only one of them set: the server refuses to start.

The contract with payments-api lives in ``lib/auth/internal_company_context.rb``
and ``app/controllers/concerns/internal_authenticable.rb``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from mcp.server.lowlevel.server import request_ctx
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

ENV_TOKEN = "CONEKTA_MCP_INTERNAL_TOKEN"
ENV_JWT_SECRET = "PAYMENTS_API_JWT_SECRET"
ENV_BASE_URL = "PAYMENTS_API_INTERNAL_URL"
ENV_CALLER = "CONEKTA_MCP_INTERNAL_CALLER"
DEFAULT_CALLER = "conekta-payment-agent"

COMPANY_ID_HEADER = "X-Company-Id"
COMPANY_CONTEXT_HEADER = "X-Company-Context"
INTERNAL_API_PREFIX = "/internal/api"

# The bot only creates payment links. Every tool here must map to a controller in
# payments-api's InternalAuthenticable::ALLOWED_CONTROLLER_GROUPS.
INTERNAL_ALLOWED_TOOLS = frozenset({"create_checkout"})

# payment-agent-backend requested the private key with livemode=true, so the bot
# has always created live checkouts. Keep that behavior; changing it is a separate decision.
INTERNAL_LIVEMODE = True

MIN_TOKEN_LENGTH = 32
JWT_TTL_SECONDS = 60
JWT_ISSUER = "conekta-mcp"
COMPANY_CONTEXT_KEY_INFO = b"payments-api/internal-api/company-context"
COMPANY_CONTEXT_KEY_LENGTH = 32
COMPANY_CONTEXT_IV_LENGTH = 12

_COMPANY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SCOPE_STATE_KEY = "conekta_internal_identity"

audit_logger = logging.getLogger("conekta_mcp.audit")


@dataclass(frozen=True)
class InternalConfig:
    token: str
    jwt_secret: str
    base_url: str
    caller: str


@dataclass(frozen=True)
class InternalIdentity:
    company_id: str
    caller: str


def load_internal_config(env: Mapping[str, str] | None = None) -> InternalConfig | None:
    """Read internal mode settings. Returns None when internal mode is not configured.

    Raises:
        RuntimeError: If the configuration is incomplete or the credential is too short.
    """
    env = os.environ if env is None else env
    token = env.get(ENV_TOKEN) or ""
    jwt_secret = env.get(ENV_JWT_SECRET) or ""

    if not token and not jwt_secret:
        return None
    if not token or not jwt_secret:
        raise RuntimeError(
            f"Internal mode is half-configured: set both {ENV_TOKEN} and "
            f"{ENV_JWT_SECRET}, or neither."
        )
    if len(token) < MIN_TOKEN_LENGTH:
        raise RuntimeError(
            f"{ENV_TOKEN} must be at least {MIN_TOKEN_LENGTH} characters long."
        )

    base_url = (env.get(ENV_BASE_URL) or "").rstrip("/")
    if not base_url:
        raise RuntimeError(f"{ENV_BASE_URL} is required when internal mode is enabled.")

    return InternalConfig(
        token=token,
        jwt_secret=jwt_secret,
        base_url=base_url,
        caller=env.get(ENV_CALLER) or DEFAULT_CALLER,
    )


_config: InternalConfig | None = None


def set_internal_config(config: InternalConfig | None) -> None:
    global _config
    _config = config


def get_internal_config() -> InternalConfig | None:
    return _config


def is_internal_token(token: str) -> bool:
    """Whether ``token`` is the internal service credential (constant-time)."""
    config = _config
    if config is None or not token:
        return False
    return hmac.compare_digest(token.encode(), config.token.encode())


def authenticate_internal(
    authorization: str | None, company_id: str | None
) -> InternalIdentity | None:
    """Validate an internal mode request. Returns None if it must be rejected."""
    config = _config
    if config is None or not authorization or company_id is None:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not is_internal_token(token):
        return None
    if not _COMPANY_ID_PATTERN.fullmatch(company_id):
        return None
    return InternalIdentity(company_id=company_id, caller=config.caller)


class InternalAuthMiddleware:
    """Authenticates internal mode at the HTTP layer, before an MCP session is opened.

    A request carrying ``X-Company-Id`` is internal mode or nothing: with an invalid
    credential it gets a 401 and never falls back to public mode with that Bearer.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        company_id = headers.get(COMPANY_ID_HEADER)
        if company_id is None:
            await self.app(scope, receive, send)
            return

        identity = authenticate_internal(headers.get("authorization"), company_id)
        if identity is None:
            audit_logger.warning(
                "internal_mode rejected path=%s client=%s",
                scope.get("path"),
                _client_host(scope),
            )
            response = JSONResponse(
                {"error": "unauthorized", "message": "Invalid internal credentials."},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})[_SCOPE_STATE_KEY] = identity
        await self.app(scope, receive, send)


def _client_host(scope: Scope) -> str | None:
    client = scope.get("client")
    return client[0] if client else None


def current_internal_identity() -> InternalIdentity | None:
    """The internal identity of the MCP request being handled, if any."""
    try:
        request = request_ctx.get().request
    except LookupError:
        return None
    if request is None:
        return None
    state = getattr(request, "scope", {}).get("state") or {}
    identity = state.get(_SCOPE_STATE_KEY)
    return identity if isinstance(identity, InternalIdentity) else None


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _compact_json(data: dict) -> bytes:
    return json.dumps(data, separators=(",", ":")).encode()


def build_internal_jwt(
    jwt_secret: str, caller: str, now: int | None = None
) -> str:
    """HS256 JWT signed with payments-api's JWT_SECRET.

    payments-api's Auth::Jwt.decode does not require ``exp``, so a token without it
    would be valid forever: always set a short one.
    """
    now = int(time.time()) if now is None else now
    header = _b64url(_compact_json({"alg": "HS256", "typ": "JWT"}))
    payload = _b64url(
        _compact_json({"iss": JWT_ISSUER, "sub": caller, "exp": now + JWT_TTL_SECONDS})
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(jwt_secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url(signature)}"


def _company_context_key(jwt_secret: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=COMPANY_CONTEXT_KEY_LENGTH,
        salt=b"",
        info=COMPANY_CONTEXT_KEY_INFO,
    ).derive(jwt_secret.encode())


def seal_company_context(
    jwt_secret: str, company_id: str, livemode: bool, now: int | None = None
) -> str:
    """Build X-Company-Context as payments-api's Auth::InternalCompanyContext expects.

    base64url without padding of ``iv(12) + ciphertext + tag(16)``, AES-256-GCM over
    ``{"company_id", "livemode", "iat"}``. It expires after 5 minutes, so build one
    per request.
    """
    now = int(time.time()) if now is None else now
    payload = _compact_json({"company_id": company_id, "livemode": livemode, "iat": now})
    iv = os.urandom(COMPANY_CONTEXT_IV_LENGTH)
    sealed = AESGCM(_company_context_key(jwt_secret)).encrypt(iv, payload, None)
    return _b64url(iv + sealed)


def open_company_context(jwt_secret: str, value: str) -> dict:
    """Inverse of seal_company_context. Used by tests."""
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    iv, sealed = raw[:COMPANY_CONTEXT_IV_LENGTH], raw[COMPANY_CONTEXT_IV_LENGTH:]
    return json.loads(AESGCM(_company_context_key(jwt_secret)).decrypt(iv, sealed, None))


def internal_request_target(
    config: InternalConfig, identity: InternalIdentity, path: str
) -> tuple[str, dict[str, str]]:
    """URL and auth headers to call payments-api's /internal/api mirror of ``path``."""
    if not path.startswith("/"):
        path = f"/{path}"
    url = f"{config.base_url}{INTERNAL_API_PREFIX}{path}"
    headers = {
        "Authorization": f"Bearer {build_internal_jwt(config.jwt_secret, config.caller)}",
        COMPANY_CONTEXT_HEADER: seal_company_context(
            config.jwt_secret, identity.company_id, INTERNAL_LIVEMODE
        ),
    }
    return url, headers


def configure_audit_logging() -> None:
    """Make sure internal mode audit lines reach stdout regardless of root config."""
    if audit_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
