from collections import deque
from typing import Optional, List, Dict
from config import Config


class MusicQueue:
    """
    Per-chat music queue.
    Internal structure per chat_id:
        {
          "queue": deque([track, track, ...]),
          "playing": bool
        }
    """

    def __init__(self):
        self._data: Dict[int, dict] = {}

    def _ensure(self, chat_id: int):
        if chat_id not in self._data:
            self._data[chat_id] = {"queue": deque(), "playing": False}

    # ── Add ───────────────────────────────────────────────────────────────
    def add(self, chat_id: int, track: dict) -> bool:
        self._ensure(chat_id)
        if len(self._data[chat_id]["queue"]) >= Config.MAX_QUEUE_SIZE:
            return False
        self._data[chat_id]["queue"].append(track)
        return True

    # ── Current (peek at front) ───────────────────────────────────────────
    def current(self, chat_id: int) -> Optional[dict]:
        self._ensure(chat_id)
        q = self._data[chat_id]["queue"]
        return q[0] if q else None

    # ── Advance queue ─────────────────────────────────────────────────────
    def next(self, chat_id: int) -> Optional[dict]:
        self._ensure(chat_id)
        q = self._data[chat_id]["queue"]
        if q:
            q.popleft()
        return q[0] if q else None

    # ── Full queue list ───────────────────────────────────────────────────
    def get_queue(self, chat_id: int) -> List[dict]:
        self._ensure(chat_id)
        return list(self._data[chat_id]["queue"])

    # ── Size ──────────────────────────────────────────────────────────────
    def size(self, chat_id: int) -> int:
        self._ensure(chat_id)
        return len(self._data[chat_id]["queue"])

    # ── Playing state ─────────────────────────────────────────────────────
    def is_playing(self, chat_id: int) -> bool:
        self._ensure(chat_id)
        return self._data[chat_id]["playing"]

    def set_playing(self, chat_id: int, state: bool):
        self._ensure(chat_id)
        self._data[chat_id]["playing"] = state

    # ── Clear ─────────────────────────────────────────────────────────────
    def clear(self, chat_id: int):
        self._ensure(chat_id)
        self._data[chat_id]["queue"].clear()
        self._data[chat_id]["playing"] = False
