from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.frontend_api.routes import router
from backend.frontend_api import event_bus

from backend.autonomy.auto_scheduler import AutoScheduler
from backend.intelligence.economic_controller import EconomicController

from backend.database import get_db
from backend.db_init import initialize_all_tables
from backend.auth import verify_admin_token
from backend.system.observability import set_actor, set_request_id
import uuid

import asyncio
import os
from dotenv import load_dotenv
import time

load_dotenv()

# ======================================
# APP INIT
# ======================================

app = FastAPI(title="Nova AI")

# --------------------------------------
# CORS
# --------------------------------------

raw_origins = os.getenv(
    "NOVA_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://localhost:8000",
)
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------
# ROUTES
# --------------------------------------

app.include_router(router, prefix="/api")

# ======================================
# MIDDLEWARE: AUTH + RATE LIMIT
# ======================================

_AUTH_EXEMPT = {
    "/api/login",
    "/api/status",
    "/api/system/health",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api") and path not in _AUTH_EXEMPT:
            auth = request.headers.get("authorization") or ""
            token = ""
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1].strip()
            if not token:
                return JSONResponse({"detail": "Missing authentication"}, status_code=401)
            try:
                info = verify_admin_token(token)
                set_actor(str(info.get("username") or ""))
            except Exception:
                return JSONResponse({"detail": "Invalid authentication"}, status_code=401)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory fixed-window limiter (per-IP, per-path).
    """

    def __init__(self, app, *, window_sec: int = 60, max_requests: int = 120):
        super().__init__(app)
        self.window_sec = int(window_sec)
        self.max_requests = int(max_requests)
        self._buckets: dict[tuple[str, str, int], int] = {}

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now_bucket = int(time.time()) // self.window_sec
        key = (ip, path, now_bucket)
        self._buckets[key] = int(self._buckets.get(key, 0)) + 1
        if self._buckets[key] > self.max_requests:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(rid)
        resp = await call_next(request)
        resp.headers["x-request-id"] = rid
        return resp


app.add_middleware(RequestIdMiddleware)

# ======================================
# STARTUP
# ======================================

scheduler = None


@app.on_event("startup")
async def startup():

    print("🚀 Starting Nova System")

    # -------------------------
    # DATABASE
    # -------------------------

    # Ensure schema exists (idempotent).
    initialize_all_tables(reset=False)
    with get_db() as conn:
        _ = conn.cursor()

    # -------------------------
    # EVENT BUS
    # -------------------------

    event_bus.init_event_bus()

    asyncio.create_task(event_bus.event_dispatcher())

    # -------------------------
    # ECONOMIC ENGINE
    # -------------------------

    controller = EconomicController()

    global scheduler
    scheduler = AutoScheduler()

    scheduler.start()

    print("✅ Nova Started")


# ======================================
# WEBSOCKET
# ======================================

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Token expected via query param (browser WebSocket cannot set custom Authorization header reliably).
    token = (ws.query_params.get("token") or "").strip()
    try:
        verify_admin_token(token)
    except Exception:
        await ws.close(code=1008)
        return

    await ws.accept()
    event_bus.register(ws)

    try:
        while True:
            await ws.receive_text()

    except Exception:
        pass

    finally:
        event_bus.unregister(ws)