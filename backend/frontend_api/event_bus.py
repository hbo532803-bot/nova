import json
import asyncio

_clients = set()
_queue: asyncio.Queue | None = None


def init_event_bus():
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()


def register(ws):
    _clients.add(ws)


def unregister(ws):
    _clients.discard(ws)


async def event_dispatcher():
    assert _queue is not None

    while True:
        event = await _queue.get()
        payload = json.dumps(event)

        dead = []
        for ws in list(_clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            _clients.discard(ws)


def broadcast(event: dict):
    """
    Sync-safe broadcast entry point.
    """
    if _queue is None:
        return
    try:
        _queue.put_nowait(event)
    except Exception:
        pass
