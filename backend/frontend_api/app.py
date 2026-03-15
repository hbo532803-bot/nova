from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.frontend_api.routes import router
from backend.frontend_api import event_bus

from backend.autonomy.auto_scheduler import AutoScheduler
from backend.intelligence.economic_controller import EconomicController

from backend.database import get_db

import asyncio
from dotenv import load_dotenv

load_dotenv()

# ======================================
# APP INIT
# ======================================

app = FastAPI(title="Nova AI")

# --------------------------------------
# CORS
# --------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------
# ROUTES
# --------------------------------------

app.include_router(router, prefix="/api")

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

    with get_db() as conn:
       cursor = conn.cursor()

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

    await ws.accept()

    event_bus.register(ws)

    try:
        while True:
            await ws.receive_text()

    except Exception:
        pass

    finally:
        event_bus.unregister(ws)