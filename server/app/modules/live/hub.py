import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Literal
from weakref import WeakKeyDictionary

from fastapi import WebSocket

from app.core.clock import utc_now

TeamData = Literal["scorecard", "issues", "todos"]


class TeamHub:
    def __init__(self) -> None:
        self.sockets: dict[str, set[WebSocket]] = defaultdict(set)
        self.locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.empty_since: dict[str, datetime] = {}

    @asynccontextmanager
    async def in_order(self, team_id: str) -> AsyncIterator[None]:
        async with self.locks[team_id]:
            yield

    def add(self, team_id: str, websocket: WebSocket) -> None:
        self.sockets[team_id].add(websocket)
        self.empty_since.pop(team_id, None)

    def remove(self, team_id: str, websocket: WebSocket) -> None:
        self.sockets[team_id].discard(websocket)
        if self.is_empty(team_id):
            self.empty_since.setdefault(team_id, utc_now())

    def is_empty(self, team_id: str) -> bool:
        return not self.sockets[team_id]

    def nobody_there_since(self, team_id: str) -> datetime:
        return self.empty_since.setdefault(team_id, utc_now())

    async def send(self, team_id: str, message: dict[str, Any]) -> None:
        sockets = list(self.sockets[team_id])
        results = await asyncio.gather(*(socket.send_json(message) for socket in sockets), return_exceptions=True)
        for socket, result in zip(sockets, results, strict=True):
            if isinstance(result, Exception):
                self.remove(team_id, socket)


hubs: WeakKeyDictionary[asyncio.AbstractEventLoop, TeamHub] = WeakKeyDictionary()


def current_hub() -> TeamHub:
    return hubs.setdefault(asyncio.get_running_loop(), TeamHub())


async def publish_change(team_id: str, what: TeamData) -> None:
    await current_hub().send(team_id, {"type": "changed", "what": what})
