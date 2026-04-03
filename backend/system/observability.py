from __future__ import annotations

import contextvars
from typing import Optional


_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("nova_request_id", default="")
_actor: contextvars.ContextVar[str] = contextvars.ContextVar("nova_actor", default="")


def set_request_id(rid: str) -> None:
    _request_id.set(rid or "")


def get_request_id() -> str:
    return _request_id.get()


def set_actor(actor: str) -> None:
    _actor.set(actor or "")


def get_actor() -> str:
    return _actor.get()


def snapshot() -> dict:
    return {"request_id": get_request_id(), "actor": get_actor()}

