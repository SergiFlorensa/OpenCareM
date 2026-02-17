"""In-process write lock for chat sessions with stale lock cleanup."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Condition
from typing import Iterator


@dataclass(frozen=True)
class SessionLockHandle:
    """Metadata for an acquired session lock."""

    lock_key: str
    owner: str
    stale_reclaimed: bool


class SessionWriteLock:
    """Cooperative in-memory lock keyed by chat session."""

    _condition = Condition()
    _owners: dict[str, tuple[str, float]] = {}

    @classmethod
    @contextmanager
    def acquire(
        cls,
        *,
        lock_key: str,
        owner: str,
        timeout_seconds: float = 2.0,
        stale_after_seconds: float = 30.0,
    ) -> Iterator[SessionLockHandle]:
        stale_reclaimed = False
        deadline = time.monotonic() + max(0.1, timeout_seconds)
        key = lock_key.strip() or "chat-session"
        owner_id = owner.strip() or "owner"

        with cls._condition:
            while True:
                now = time.monotonic()
                current = cls._owners.get(key)
                if current is None:
                    cls._owners[key] = (owner_id, now)
                    break

                current_owner, acquired_at = current
                if now - acquired_at > max(1.0, stale_after_seconds):
                    cls._owners[key] = (owner_id, now)
                    stale_reclaimed = True
                    break

                remaining = deadline - now
                if remaining <= 0:
                    raise TimeoutError(
                        f"Session lock timeout for key '{key}' (held by '{current_owner}')."
                    )
                cls._condition.wait(timeout=min(remaining, 0.2))

        try:
            yield SessionLockHandle(
                lock_key=key,
                owner=owner_id,
                stale_reclaimed=stale_reclaimed,
            )
        finally:
            with cls._condition:
                current = cls._owners.get(key)
                if current is not None and current[0] == owner_id:
                    del cls._owners[key]
                    cls._condition.notify_all()
