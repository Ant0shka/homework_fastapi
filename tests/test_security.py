from __future__ import annotations

import pytest

from app.core import security


def test_password_hash_roundtrip() -> None:
    h = security.get_password_hash("my-secret-password")
    assert security.verify_password("my-secret-password", h) is True
    assert security.verify_password("other", h) is False


def test_create_and_decode_token() -> None:
    token = security.create_access_token("42")
    assert security.decode_token(token) == "42"


def test_decode_token_invalid() -> None:
    assert security.decode_token("not-a-jwt") is None
    assert security.decode_token("") is None


def test_decode_token_missing_sub(mocker) -> None:
    mocker.patch("app.core.security.jwt.decode", return_value={"foo": "bar"})
    assert security.decode_token("ignored") is None
