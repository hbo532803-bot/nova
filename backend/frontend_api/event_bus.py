import json
import asyncio
import logging
import os
import time

from backend.system.observability import get_request_id
_clients = set()
_queue: asyncio.Queue | None = None
_dropped = 0
_initialized = False
_last_overflow_warn = 0.0

_log = logging.getLogger("nova.event_bus")


def stats() -> dict:
    qsize = _queue.qsize() if _queue is not None else 0
    maxsize = _queue.maxsize if _queue is not None else 0
    return {
        "initialized": bool(_initialized),
        "clients": len(_clients),
        "queue_size": qsize,
        "queue_max": maxsize,
        "dropped": int(_dropped),
    }


def init_event_bus():
    global _queue, _initialized
    if _queue is None:
        maxsize = int(os.getenv("NOVA_EVENTBUS_MAX_QUEUE", "1000"))
        _queue = asyncio.Queue(maxsize=max(1, maxsize))
    _initialized = True


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
    global _dropped, _last_overflow_warn
    # Propagate request id into event payload when present.
    try:
        if "request_id" not in event:
            rid = get_request_id()
            if rid:
                event = {**event, "request_id": rid}
    except Exception:
        pass
    if _queue is None or not _initialized:
        _dropped += 1
        now = time.time()
        if now - _last_overflow_warn > 5:
            _last_overflow_warn = now
            _log.warning("event_bus not initialized; dropping event", extra={"dropped": _dropped, "event_type": event.get("type")})
        return False
    try:
        _queue.put_nowait(event)
        return True
    except asyncio.QueueFull:
        _dropped += 1
        now = time.time()
        if now - _last_overflow_warn > 5:
            _last_overflow_warn = now
            _log.warning("event_bus queue full; dropping event", extra={"dropped": _dropped, "queue_max": _queue.maxsize, "event_type": event.get("type")})
        return False
    except Exception as e:
        _dropped += 1
        _log.exception("event_bus broadcast failed; dropping event", extra={"error": str(e), "dropped": _dropped})
        return False
