import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("gis.ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client connected (%d total)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("Client disconnected (%d total)", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self._connections.discard(connection)

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
