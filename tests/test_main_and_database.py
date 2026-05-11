from __future__ import annotations

import sqlite3

import pytest
from sqlalchemy import text

import app.main as main_mod


@pytest.mark.asyncio
async def test_app_lifespan(monkeypatch) -> None:
    from app.database import engine as real_engine

    class _EngineFacade:
        def begin(self):
            return real_engine.begin()

        async def dispose(self) -> None:
            return None

    monkeypatch.setattr(main_mod, "engine", _EngineFacade())
    async with main_mod.lifespan(main_mod.app):
        pass


def test_sqlite_fk_connect_hook() -> None:
    from app.database import _sqlite_fk

    conn = sqlite3.connect(":memory:")
    try:
        _sqlite_fk(conn, None)
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys")
        assert cur.fetchone()[0] == 1
        cur.close()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_sqlite_pragma_foreign_keys_enabled() -> None:
    from app.database import engine

    async with engine.connect() as conn:
        r = await conn.execute(text("PRAGMA foreign_keys"))
        row = r.fetchone()
        assert row is not None
        assert int(row[0]) == 1
