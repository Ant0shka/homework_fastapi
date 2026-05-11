from __future__ import annotations

from app.core import cache as task_cache


def test_cache_version_bump_increments() -> None:
    task_cache.reset_caches_for_tests()
    assert task_cache.user_cache_version(7) == 0
    task_cache.bump_user_cache_version(7)
    assert task_cache.user_cache_version(7) == 1


def test_list_top_cache_roundtrip() -> None:
    task_cache.reset_caches_for_tests()
    key_list = (1, 0, "list", "title", "asc")
    task_cache.list_cache_set(key_list, [{"id": 1}])
    assert task_cache.list_cache_get(key_list) == [{"id": 1}]
    assert task_cache.list_cache_get((9, 0, "list", "title", "asc")) is None

    key_top = (1, 0, "top", 3)
    task_cache.top_cache_set(key_top, [{"id": 2}])
    assert task_cache.top_cache_get(key_top) == [{"id": 2}]
