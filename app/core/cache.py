"""TTL cache for read-heavy endpoints; invalidated per-user on task mutations."""

from collections import defaultdict

from cachetools import TTLCache

from app.core.config import settings

_user_versions: dict[int, int] = defaultdict(int)

_list_cache: TTLCache[tuple, list] = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)
_top_cache: TTLCache[tuple, list] = TTLCache(maxsize=128, ttl=settings.cache_ttl_seconds)


def bump_user_cache_version(user_id: int) -> None:
    _user_versions[user_id] += 1


def user_cache_version(user_id: int) -> int:
    return _user_versions[user_id]


def list_cache_get(key: tuple) -> list | None:
    return _list_cache.get(key)


def list_cache_set(key: tuple, value: list) -> None:
    _list_cache[key] = value


def top_cache_get(key: tuple) -> list | None:
    return _top_cache.get(key)


def top_cache_set(key: tuple, value: list) -> None:
    _top_cache[key] = value


def reset_caches_for_tests() -> None:
    _list_cache.clear()
    _top_cache.clear()
    _user_versions.clear()
