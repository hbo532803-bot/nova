from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.frontend_api.routes import router
from backend.frontend_api import event_bus
from backend.autonomy.auto_scheduler import AutoScheduler
from backend.intelligence.economic_controller import EconomicController
from backend.database import init_db
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# ROUTER (ONLY ONCE)
# -------------------------

app.include_router(router, prefix="/api")

# -------------------------
# STARTUP EVENTS
# -------------------------

@app.on_event("startup")
async def startup():
    init_db()
    event_bus.init_event_bus()
    asyncio.create_task(event_bus.event_dispatcher())

    controller = EconomicController()
    scheduler = AutoScheduler(controller)
    scheduler.start()

# -------------------------
# WEBSOCKET
# -------------------------

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