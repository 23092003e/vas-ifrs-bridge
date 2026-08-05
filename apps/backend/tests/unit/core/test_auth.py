from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt
from jose.utils import base64url_encode

from app.core import auth

ISSUER = "https://project.supabase.co/auth/v1"


def _claims(**overrides: object) -> dict[str, object]:
    claims: dict[str, object] = {
        "sub": "user-1",
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 300,
    }
    claims.update(overrides)
    return claims


def _settings(*, service_key: str, jwt_secret: str) -> SimpleNamespace:
    return SimpleNamespace(
        supabase_url="https://project.supabase.co",
        supabase_service_role_key=service_key,
        supabase_jwt_secret=jwt_secret,
        supabase_jwt_audience="authenticated",
    )


def _rsa_signing_material(kid: str) -> tuple[bytes, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()

    def encoded(value: int) -> str:
        raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
        return base64url_encode(raw).decode()

    return private_pem, {
        "kty": "RSA",
        "kid": kid,
        "alg": "RS256",
        "use": "sig",
        "n": encoded(public_numbers.n),
        "e": encoded(public_numbers.e),
    }


@pytest.mark.asyncio
async def test_service_role_key_is_not_accepted_as_hs256_signing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reusing the service-role token as a signing secret must not authenticate users."""
    monkeypatch.setattr(auth, "settings", _settings(service_key="service-role", jwt_secret=""))
    token = jwt.encode(_claims(), "service-role", algorithm="HS256")

    with pytest.raises(JWTError):
        await auth.verify_jwt(token)


@pytest.mark.asyncio
async def test_legacy_hs256_requires_configured_secret_and_expected_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing issuer/audience verification must invalidate this known-good project token."""
    monkeypatch.setattr(
        auth,
        "settings",
        _settings(service_key="not-the-signing-secret", jwt_secret="legacy-jwt-secret"),
    )
    token = jwt.encode(_claims(), "legacy-jwt-secret", algorithm="HS256")

    claims = await auth.verify_jwt(token)

    assert claims["sub"] == "user-1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claim_overrides",
    [
        {"aud": "another-service"},
        {"iss": "https://attacker.example/auth/v1"},
        {"sub": ""},
    ],
)
async def test_hs256_rejects_wrong_project_claims_or_missing_subject(
    monkeypatch: pytest.MonkeyPatch,
    claim_overrides: dict[str, object],
) -> None:
    """Weakening any required project claim must allow an invalid token through this test."""
    monkeypatch.setattr(
        auth,
        "settings",
        _settings(service_key="legacy-jwt-secret", jwt_secret="legacy-jwt-secret"),
    )
    token = jwt.encode(_claims(**claim_overrides), "legacy-jwt-secret", algorithm="HS256")

    with pytest.raises(JWTError):
        await auth.verify_jwt(token)


@pytest.mark.asyncio
async def test_unknown_kid_refreshes_jwks_once_before_rejecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing the forced refresh must break tokens signed immediately after key rotation."""
    monkeypatch.setattr(auth, "settings", _settings(service_key="service-role", jwt_secret=""))
    private_pem, public_jwk = _rsa_signing_material("rotated-key")
    token = jwt.encode(_claims(), private_pem, algorithm="RS256", headers={"kid": "rotated-key"})
    refresh_calls: list[bool] = []

    async def fake_fetch_jwks(*, force_refresh: bool = False) -> dict[str, object]:
        refresh_calls.append(force_refresh)
        return {"keys": [public_jwk]} if force_refresh else {"keys": []}

    monkeypatch.setattr(auth, "_fetch_jwks", fake_fetch_jwks)

    claims = await auth.verify_jwt(token)

    assert claims["sub"] == "user-1"
    assert refresh_calls == [False, True]
