from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
import uuid
from datetime import datetime, timedelta

from backend.frontend_api.event_bus import broadcast

from backend.memory.goal_memory import list_goals, primary_goal
from backend.memory.reflection_memory import ReflectionMemory

from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.self_analyzer import SelfAnalyzer
from backend.runtime.command_queue import CommandQueue
from backend.intelligence.opportunity_engine import OpportunityEngine

from backend.system.permission_gate import permission_gate
from backend.system.kill_switch import kill_switch
from backend.system.state_store import StateStore
from backend.system.validation import validate_architecture
from backend.intelligence.playbooks.library import list_playbooks
from backend.intelligence.experiment_analytics import ExperimentAnalytics
from backend.system.stability import SystemStability
import json
from pathlib import Path
import os
import requests

from backend.tools.rollback_manager import rollback_last

from backend.auth import authenticate_user, create_access_token, get_current_admin
from backend.system.audit_log import audit_log

from backend.database import get_db

from backend.core.nova_core import get_nova_core
from backend.nova import Nova
from backend.services.requirement_engine import RequirementEngineService
from backend.services.result_collector import ResultCollector
from backend.services.delivery_service import DeliveryService
from backend.intelligence.traffic_engine import TrafficEngine
from backend.intelligence.signal_engine import SignalEngine
from backend.intelligence.metrics_engine import MetricsEngine
import logging
import threading
import ast

router = APIRouter()

STATE = {"status": "IDLE"}
PENDING_DIFF = {}
_requirement_engine = RequirementEngineService()
_result_collector = ResultCollector()
_delivery_service = DeliveryService()
_traffic_engine = TrafficEngine()
_signal_engine = SignalEngine()
_metrics_engine = MetricsEngine()
_order_logger = logging.getLogger(__name__)


def _safe_json_parse(raw):
    if isinstance(raw, (dict, list)):
        return raw
    text = str(raw or "").strip()
    if not text:
        return {}
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text)
        except Exception:
            continue
    return {"raw": text}




def _traffic_source(value: str) -> str:
    t = (value or "").strip().lower()
    if "ads" in t or "google" in t or "meta" in t:
        return "ads"
    if "organic" in t or "seo" in t:
        return "organic"
    if "manual" in t or "direct" in t:
        return "manual"
    return "unknown"


def _update_order(order_id: str, **fields):
    if not fields:
        return
    pairs = list(fields.items()) + [("updated_at", datetime.utcnow())]
    set_clause = ", ".join([f"{k}=?" for k, _ in pairs])
    values = [v for _, v in pairs] + [order_id]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE customer_orders SET {set_clause} WHERE id=?", values)
        conn.commit()


def _extract_mission_id(execution_result: dict) -> str:
    if not isinstance(execution_result, dict):
        return ""
    if execution_result.get("mission_id"):
        return str(execution_result.get("mission_id"))
    decision = execution_result.get("decision") or {}
    if isinstance(decision, dict) and decision.get("mission_id"):
        return str(decision.get("mission_id"))
    nested = execution_result.get("result") or {}
    if isinstance(nested, dict) and nested.get("mission_id"):
        return str(nested.get("mission_id"))
    return ""


def _run_order_execution(order_id: str, command: str):
    try:
        _update_order(order_id, status="RUNNING", progress=35)
        execution_result = get_nova_core().handle_command(command)
        mission_id = _extract_mission_id(execution_result)

        final_result = None
        if mission_id:
            aggregated = _result_collector.collect_outputs(mission_id=mission_id)
            final_result = _delivery_service.build_final_result(aggregated, type_hint=command)

        payload = {
            "execution_result": execution_result,
            "final_result": final_result,
            "mission_id": mission_id,
        }
        _update_order(
            order_id,
            status="COMPLETED",
            progress=100,
            mission_id=mission_id or None,
            execution_result=json.dumps(payload),
        )
    except Exception:
        _order_logger.exception("order execution failed")
        _update_order(
            order_id,
            status="COMPLETED",
            progress=100,
            execution_result=json.dumps({"error": "order_execution_failed", "final_result": None}),
        )

# -------------------------------------------------
# Utility
# -------------------------------------------------

def reset_run_state():
    permission_gate.reset()
    PENDING_DIFF.clear()


# -------------------------------------------------
# Reflection Recorder
# -------------------------------------------------

def record_cycle(goal, decision, outcome, success):

    try:

        reflection = ReflectionMemory()
        engine = ConfidenceEngine()
        score = engine.get_score()

        reflection.record_reflection({
            "cycle_id": str(uuid.uuid4()),
            "primary_goal_snapshot": primary_goal(),
            "input_objective": goal,
            "refined_intent": goal,
            "plan_summary": str(decision),
            "execution_result": "success" if success else outcome,
            "success": success,

            "reasoning_depth_score": 1,
            "alignment_score": 90 if success else 60,
            "complexity_score": 1,
            "risk_score": 30 if success else 70,

            "assumptions_made": [],
            "assumptions_invalidated": [],

            "decision_quality": "high" if success else "blocked",
            "mistake_type": "" if success else outcome,
            "missed_simplification": "",

            "confidence_before": score,
            "confidence_after": score,
            "confidence_delta": 0,

            "system_stress_level": "normal",
            "architecture_limitation_detected": False,
            "limitation_details": "",

            "meta_reasoner_override": False,
            "admin_intervention": False,

            "improvement_suggestions": [],
            "pattern_tags": []
        })

    except Exception as e:
        print("Reflection failed:", e)


# -------------------------------------------------
# AUTH
# -------------------------------------------------

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=60)
    )

    return {"access_token": access_token, "token_type": "bearer"}


# -------------------------------------------------
# STATUS
# -------------------------------------------------

@router.get("/status")
def get_status():

    engine = ConfidenceEngine()

    return {
        "status": "running",
        "confidence": engine.get_score()
    }


@router.get("/confidence")
def get_confidence(admin=Depends(get_current_admin)):
    engine = ConfidenceEngine()
    return engine.get_state()


@router.get("/system/state")
def get_system_state(admin=Depends(get_current_admin)):
    store = StateStore()
    return store.get().__dict__


# -------------------------------------------------
# SYSTEM HEALTH
# -------------------------------------------------

@router.get("/system/health")
def system_health():

    engine = ConfidenceEngine()

    return {
        "status": "healthy",
        "confidence": engine.get_score(),
        "kill_switch": kill_switch.is_triggered(),
        "timestamp": datetime.utcnow()
    }

@router.get("/system/self-analysis")
def system_self_analysis(admin=Depends(get_current_admin)):

    analyzer = SelfAnalyzer()
    return analyzer.generate_system_report()


@router.get("/system/validate")
def system_validate(admin=Depends(get_current_admin)):
    return validate_architecture()


# -------------------------------------------------
# SYSTEM PAUSE
# -------------------------------------------------

@router.post("/system/pause")
def pause_system(admin=Depends(get_current_admin)):

    kill_switch.trigger()
    audit_log(actor=admin.get("username"), action="SYSTEM_PAUSE")

    return {"status": "paused"}


# -------------------------------------------------
# SYSTEM RESUME
# -------------------------------------------------

@router.post("/system/resume")
def resume_system(admin=Depends(get_current_admin)):

    kill_switch.reset()
    audit_log(actor=admin.get("username"), action="SYSTEM_RESUME")

    return {"status": "running"}


# -------------------------------------------------
# MEMORY
# -------------------------------------------------

@router.get("/memory/goals")
def get_goals():
    return list_goals()


# -------------------------------------------------
# RUN
# -------------------------------------------------

@router.post("/run")
def run(request: dict, admin=Depends(get_current_admin)):

    goal = request.get("goal")

    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")

    broadcast({
        "type": "log",
        "level": "info",
        "message": "Run requested"
    })

    audit_log(actor=admin.get("username"), action="RUN", target="nova_core", payload={"goal": goal})
    result = get_nova_core().handle_command(goal)

    broadcast({
        "type": "log",
        "level": "info",
        "message": "NovaCore execution finished"
    })

    return result


@router.post("/requirements/intake")
def requirement_intake(payload: dict, admin=Depends(get_current_admin)):
    """
    User-facing requirement intake.
    Optional execution remains inside NovaCore -> Supervisor -> ExecutionEngine pipeline.
    """
    user_input = (payload.get("input") or "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="input is required")

    provided = payload.get("details") or {}
    execute = bool(payload.get("execute", False))

    requirement = _requirement_engine.build_requirement(user_input=user_input, provided=provided)
    command = get_nova_core().requirement_to_command(requirement)

    response = {
        "requirement": requirement,
        "command": command,
        "executed": False,
    }

    if execute:
        response["execution_result"] = get_nova_core().handle_command(command)
        response["executed"] = True

    return response


@router.post("/order/create")
def order_create(payload: dict):
    user_input = (payload.get("input") or "").strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="input is required")

    details = payload.get("details") or {}
    requirement = _requirement_engine.build_requirement(user_input=user_input, provided=details)
    offers = requirement.get("details", {}).get("offers", [])

    order_id = str(uuid.uuid4())
    mission_id = f"order-{order_id}"
    estimated_pricing = {str(o.get("tier")): o.get("estimated_price") for o in offers if o.get("tier")}
    execution_plan_preview = [
        {
            "tier": o.get("tier"),
            "timeline": (o.get("execution_scope") or {}).get("timeline"),
            "deliverables": (o.get("execution_scope") or {}).get("deliverables", []),
        }
        for o in offers
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO customer_orders (
                id, mission_id, user_input, service, requirement_json, offers_json, status, progress, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 10, ?)
            """,
            (
                order_id,
                mission_id,
                user_input,
                requirement.get("service"),
                json.dumps(requirement),
                json.dumps(offers),
                datetime.utcnow(),
            ),
        )
        conn.commit()

    return {
        "order_id": order_id,
        "mission_id": mission_id,
        "service": requirement.get("service"),
        "offers": offers,
        "estimated_pricing": estimated_pricing,
        "execution_plan_preview": execution_plan_preview,
    }


@router.post("/order/confirm")
def order_confirm(payload: dict):
    order_id = str(payload.get("order_id") or "").strip()
    selected_plan = str(payload.get("selected_plan") or "").strip().upper()
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    if selected_plan not in {"BASIC", "STANDARD", "PREMIUM"}:
        raise HTTPException(status_code=400, detail="selected_plan must be BASIC/STANDARD/PREMIUM")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_orders WHERE id=?", (order_id,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="order not found")

    status = str(row["status"] or "")
    if status in {"RUNNING", "COMPLETED"}:
        raise HTTPException(status_code=409, detail=f"order already {status.lower()}")

    requirement = _safe_json_parse(row["requirement_json"])
    offers = _safe_json_parse(row["offers_json"])
    offer_tiers = {str(o.get("tier")).upper() for o in offers if isinstance(o, dict)}
    if selected_plan not in offer_tiers:
        raise HTTPException(status_code=400, detail=f"selected_plan not offered: {selected_plan}")

    service = str((requirement or {}).get("service") or row["service"] or "consultation")
    goal = str((requirement or {}).get("goal") or row["user_input"] or "").strip()
    command = f"run mission {service}: {goal} [{selected_plan}]"

    _update_order(order_id, selected_plan=selected_plan, command_text=command, status="PENDING", progress=20)
    threading.Thread(target=_run_order_execution, args=(order_id, command), daemon=True).start()

    return {"ok": True, "order_id": order_id, "status": "RUNNING", "selected_plan": selected_plan}


@router.get("/order/status/{id}")
def order_status(id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_orders WHERE id=?", (id,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="order not found")

    result_payload = _safe_json_parse(row["execution_result"])
    return {
        "order_id": str(row["id"]),
        "mission_id": str(row["mission_id"] or ""),
        "status": str(row["status"] or "PENDING").lower(),
        "progress": int(row["progress"] or 0),
        "selected_plan": row["selected_plan"],
        "result": result_payload if str(row["status"] or "").upper() in {"COMPLETED"} else None,
    }


@router.get("/order/result/{id}")
def order_result(id: str, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mission_id, execution_result FROM customer_orders WHERE id=?", (id,))
        order_row = cursor.fetchone()
    if order_row:
        mission_id = str(order_row["mission_id"] or "")
        if mission_id:
            aggregated = _result_collector.collect_outputs(mission_id=mission_id)
            return _delivery_service.build_final_result(aggregated)
        stored = _safe_json_parse(order_row["execution_result"])
        if isinstance(stored, dict) and stored.get("final_result"):
            return stored["final_result"]

    aggregated = _result_collector.collect_outputs(order_id=id)
    resolved_mission_id = aggregated.get("mission_id")
    if not resolved_mission_id:
        # id may already be a mission_id
        aggregated = _result_collector.collect_outputs(mission_id=id)
    return _delivery_service.build_final_result(aggregated)


@router.post("/leads")
def capture_lead(payload: dict):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip()
    source = (payload.get("source") or "website_form").strip()
    mission_id = (payload.get("mission_id") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not email and not phone:
        raise HTTPException(status_code=400, detail="email or phone is required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (mission_id, name, email, phone, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mission_id, name, email, phone, source),
        )
        lead_id = int(cursor.lastrowid)
        conn.commit()

    logging.getLogger(__name__).info("NEW_LEAD_CAPTURED", extra={"lead_id": lead_id, "mission_id": mission_id, "source": source})
    _signal_engine.safe_track_event(
        event_type="lead",
        mission_id=mission_id,
        experiment_id=int(payload.get("experiment_id")) if payload.get("experiment_id") else None,
        source=source,
        session_id=str(payload.get("session_id") or ""),
        data_source="real",
        traffic_source=_traffic_source(source),
        lead_quality=str(payload.get("lead_quality") or "medium"),
        conversion_to_payment=False,
        reason="lead_capture_api",
        metadata={"lead_id": lead_id},
    )
    webhook = (os.getenv("NOVA_LEAD_WEBHOOK") or "").strip()
    hook_sent = False
    if webhook:
        try:
            requests.post(
                webhook,
                json={"lead_id": lead_id, "mission_id": mission_id, "name": name, "email": email, "phone": phone, "source": source},
                timeout=3,
            )
            hook_sent = True
        except Exception:
            logging.getLogger(__name__).exception("lead webhook send failed")
    return {"ok": True, "lead_id": lead_id, "hook_ready": True, "hook_sent": hook_sent}


@router.get("/landing/{mission_id}", response_class=HTMLResponse)
def mission_landing(mission_id: str, ref: str | None = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key=?", (f"mission_site_{mission_id}",))
        row = cursor.fetchone()
    if not row or not row["value"]:
        raise HTTPException(status_code=404, detail="mission landing not found")
    path = Path(str(row["value"]))
    if not path.exists():
        raise HTTPException(status_code=404, detail="landing file missing")
    _traffic_engine.record_visit(mission_id=mission_id, source="landing", referral=str(ref or ""))
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.post("/checkout/simulate")
def checkout_simulate(payload: dict):
    mission_id = (payload.get("mission_id") or "").strip()
    lead_id = payload.get("lead_id")
    amount = float(payload.get("amount") or 499.0)
    source = (payload.get("source") or "landing_checkout").strip()
    if not mission_id:
        raise HTTPException(status_code=400, detail="mission_id is required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO revenue_events (mission_id, lead_id, amount, status, source)
            VALUES (?, ?, ?, 'PAID', ?)
            """,
            (mission_id, int(lead_id) if lead_id else None, amount, source),
        )
        event_id = int(cursor.lastrowid)
        conn.commit()
    _signal_engine.safe_track_event(
        event_type="payment",
        mission_id=mission_id,
        experiment_id=int(payload.get("experiment_id")) if payload.get("experiment_id") else None,
        source=source,
        session_id=str(payload.get("session_id") or ""),
        event_value=amount,
        data_source="real",
        traffic_source=_traffic_source(source),
        conversion_to_payment=True,
        reason="checkout_paid",
        metadata={"event_id": event_id, "lead_id": int(lead_id) if lead_id else None},
    )
    return {"ok": True, "event_id": event_id, "mission_id": mission_id, "amount": amount, "status": "PAID"}


@router.post("/signals/track")
def track_signal(payload: dict):
    mission_id = (payload.get("mission_id") or "").strip()
    event_type = (payload.get("event_type") or "").strip().lower()
    source = (payload.get("source") or "frontend").strip()
    if not mission_id:
        raise HTTPException(status_code=400, detail="mission_id is required")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    try:
        result = _signal_engine.track_event(
            event_type=event_type,
            mission_id=mission_id,
            experiment_id=int(payload.get("experiment_id")) if payload.get("experiment_id") else None,
            source=source,
            session_id=str(payload.get("session_id") or ""),
            event_value=float(payload.get("event_value")) if payload.get("event_value") is not None else None,
            is_simulated=bool(payload.get("is_simulated", False)),
            data_source=str(payload.get("data_source") or "").strip().lower() or None,
            traffic_source=_traffic_source(str(payload.get("traffic_source") or source)),
            lead_quality=str(payload.get("lead_quality") or "").strip().lower() or None,
            conversion_to_payment=payload.get("conversion_to_payment") if payload.get("conversion_to_payment") is not None else None,
            reason=str(payload.get("reason") or "manual_track"),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/metrics/capability")
def capability_metrics(
    mission_id: str | None = None,
    experiment_id: int | None = None,
    min_sample_threshold: int = 50,
    admin=Depends(get_current_admin),
):
    return _metrics_engine.compute(
        mission_id=mission_id,
        experiment_id=experiment_id,
        min_sample_threshold=min_sample_threshold,
    )


@router.get("/metrics/funnel")
def funnel_metrics(mission_id: str | None = None, experiment_id: int | None = None, admin=Depends(get_current_admin)):
    metrics = _metrics_engine.compute(mission_id=mission_id, experiment_id=experiment_id)
    return {
        "mission_id": mission_id,
        "experiment_id": experiment_id,
        "funnel": metrics.get("funnel", {}),
        "reliability": metrics.get("reliability", {}),
        "traffic_source": metrics.get("traffic_source", {}),
    }


@router.post("/traffic/simulate")
def simulate_traffic(payload: dict, admin=Depends(get_current_admin)):
    mission_id = (payload.get("mission_id") or "").strip()
    source = (payload.get("source") or "google_ads").strip()
    if not mission_id:
        raise HTTPException(status_code=400, detail="mission_id is required")
    result = _traffic_engine.simulate(
        mission_id=mission_id,
        source=source,
        impressions=int(payload.get("impressions") or 1000),
        ctr=float(payload.get("ctr") or 0.03),
        conversion_rate=float(payload.get("conversion_rate") or 0.12),
        lead_value=float(payload.get("lead_value") or 200.0),
        experiment_id=int(payload.get("experiment_id")) if payload.get("experiment_id") else None,
        scale_threshold=int(payload.get("scale_threshold") or 20),
    )
    return result


@router.get("/metrics/revenue")
def revenue_metrics(mission_id: str | None = None, admin=Depends(get_current_admin)):
    legacy = _traffic_engine.dashboard_metrics(mission_id=mission_id)
    capability = _metrics_engine.compute(mission_id=mission_id)
    return {
        **legacy,
        "capability": capability,
    }


# -------------------------------------------------
# COMMANDS (AI CONTROL CONSOLE)
# -------------------------------------------------

@router.post("/commands")
def submit_command(payload: dict, admin=Depends(get_current_admin)):
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(text)
    audit_log(actor=admin.get("username"), action="COMMAND_SUBMIT", target=str(cmd_id), payload={"text": text})
    return {"id": cmd_id, "status": "PENDING", "text": text}


@router.get("/commands")
def list_commands(limit: int = 20, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    return {"commands": [dict(r) for r in q.fetch_recent(limit=limit)]}


# -------------------------------------------------
# AGENTS (real DB state)
# -------------------------------------------------

@router.get("/agents")
def list_agents(status: str | None = None, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM agents WHERE status=? ORDER BY total_revenue DESC", (status,))
        else:
            cursor.execute("SELECT * FROM agents ORDER BY total_revenue DESC")
        rows = cursor.fetchall()
    return {"agents": [dict(r) for r in rows]}


@router.post("/agents/{agent_id}/hibernate")
def hibernate_agent(agent_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"hibernate agent {agent_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/agents/{agent_id}/wake")
def wake_agent(agent_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"wake agent {agent_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


# -------------------------------------------------
# ROLLBACK
# -------------------------------------------------

@router.post("/rollback/last")
def rollback(path: str, admin=Depends(get_current_admin)):

    rollback_last(path)
    audit_log(actor=admin.get("username"), action="ROLLBACK_LAST", target=path)

    broadcast({
        "type": "log",
        "level": "warn",
        "message": f"Rollback performed on {path}"
    })

    return {"ok": True}

# -------------------------------------------------
# MARKET / OPPORTUNITIES / EXPERIMENTS (mutations via command queue)
# -------------------------------------------------

@router.post("/market/scan")
def enqueue_market_scan(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("analyze market")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/strategy/learn")
def enqueue_strategy_learning(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("learn strategy")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.get("/system/stability/health")
def stability_health(admin=Depends(get_current_admin)):
    # read-only (safe), but mirrors action-based HEALTH_CHECK semantics
    return SystemStability().health()


@router.post("/system/stability/recover")
def enqueue_stability_recover(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("recover system")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.get("/analytics/experiments")
def analytics_experiments(limit: int = 50, admin=Depends(get_current_admin)):
    a = ExperimentAnalytics()
    return {"summary": a.summary(limit=limit), "experiments": a.list(limit=limit)}


@router.post("/experiments/portfolio/evaluate")
def enqueue_portfolio_evaluate(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("evaluate portfolio")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/research/run")
def enqueue_research(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("research opportunities")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/agents/factory/create")
def enqueue_agent_factory_create(payload: dict, admin=Depends(get_current_admin)):
    caps = payload.get("capabilities") or []
    if not isinstance(caps, list) or not caps:
        raise HTTPException(status_code=400, detail="capabilities list required")
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"create agent for {', '.join([str(c) for c in caps])}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/agents/factory/evolve")
def enqueue_agent_factory_evolve(admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command("evolve agents")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.get("/analytics/agents/activity")
def analytics_agent_activity(limit: int = 200, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT agent_name, action, result, created_at
            FROM agent_actions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    return {"events": [dict(r) for r in rows]}

@router.get("/analytics/agents/productivity")
def analytics_agent_productivity(days: int = 7, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT agent_name, COUNT(*) as actions
            FROM agent_actions
            WHERE created_at >= datetime('now', ?)
            GROUP BY agent_name
            ORDER BY actions DESC
            """,
            (f"-{int(days)} days",),
        )
        rows = cursor.fetchall()
    return {"days": days, "agents": [dict(r) for r in rows]}


@router.get("/analytics/confidence/trend")
def analytics_confidence_trend(limit: int = 50, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, success, confidence_before, confidence_after, created_at
            FROM reflections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    points = [dict(r) for r in rows][::-1]
    return {"points": points}


@router.get("/missions/{mission_id}/memory")
def mission_memory(mission_id: str, limit: int = 200, admin=Depends(get_current_admin)):
    from backend.memory.working_memory import WorkingMemoryStore

    return {"mission_id": mission_id, "items": WorkingMemoryStore().list(mission_id, limit=limit)}


@router.get("/knowledge/graph/summary")
def knowledge_graph_summary(admin=Depends(get_current_admin)):
    from backend.knowledge.graph_store import KnowledgeGraphStore

    return KnowledgeGraphStore().summary()


@router.get("/knowledge/graph/neighbors")
def knowledge_graph_neighbors(node_type: str, node_key: str, limit: int = 50, admin=Depends(get_current_admin)):
    from backend.knowledge.graph_store import KnowledgeGraphStore

    return KnowledgeGraphStore().neighbors(node_type, node_key, limit=limit)


@router.get("/knowledge/graph/path")
def knowledge_graph_path(
    source_type: str,
    source_key: str,
    target_type: str,
    target_key: str,
    max_depth: int = 3,
    admin=Depends(get_current_admin),
):
    from backend.knowledge.graph_store import KnowledgeGraphStore

    return KnowledgeGraphStore().find_path(source_type, source_key, target_type, target_key, max_depth=max_depth)


@router.get("/knowledge/insights")
def knowledge_insights(admin=Depends(get_current_admin)):
    from backend.knowledge.reasoner import KnowledgeGraphReasoner

    return KnowledgeGraphReasoner().insights(limit_edges=1000)


@router.get("/analytics/portfolio/health")
def portfolio_health(admin=Depends(get_current_admin)):
    from backend.intelligence.experiment_lifecycle import ExperimentLifecycleEngine

    return ExperimentLifecycleEngine().evaluate_portfolio(limit=50)


@router.get("/analytics/strategy/current")
def current_strategy(admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key='strategy_adjustments'")
        row = cursor.fetchone()
    if not row or not row["value"]:
        return {"ok": False, "strategy": None}
    try:
        return {"ok": True, "strategy": json.loads(str(row["value"]))}
    except Exception:
        return {"ok": True, "strategy": str(row["value"])}


@router.get("/cognitive/last")
def cognitive_last(admin=Depends(get_current_admin)):
    from backend.core.cognitive_cycle import CognitiveCycle

    return {"ok": True, "cognitive": CognitiveCycle().last()}


@router.get("/research/last")
def research_last(admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key='research_last'")
        row = cursor.fetchone()
    if not row or not row["value"]:
        return {"ok": False, "research": None}
    try:
        return {"ok": True, "research": json.loads(str(row["value"]))}
    except Exception:
        return {"ok": True, "research": str(row["value"])}


# -------------------------------------------------
# OPPORTUNITIES (Opportunity Engine)
# -------------------------------------------------

@router.get("/opportunities")
def list_opportunity_proposals(admin=Depends(get_current_admin)):
    eng = OpportunityEngine()
    return {"proposals": eng.list_proposals()}


@router.post("/opportunities/{proposal_id}/approve")
def approve_opportunity(proposal_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"opportunity approve {proposal_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/opportunities/{proposal_id}/reject")
def reject_opportunity(proposal_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"opportunity reject {proposal_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/opportunities/{proposal_id}/convert")
def convert_opportunity_to_experiment(proposal_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"opportunity convert {proposal_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.get("/experiments")
def list_experiments(admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM economic_experiments ORDER BY created_at DESC")
        rows = cursor.fetchall()
    return {"experiments": [dict(r) for r in rows]}


@router.get("/playbooks")
def get_playbooks(admin=Depends(get_current_admin)):
    return {"playbooks": list_playbooks()}


@router.post("/experiments/{experiment_id}/playbooks/{playbook_name}/attach")
def attach_playbook(experiment_id: int, playbook_name: str, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"attach playbook {playbook_name} to experiment {experiment_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.post("/experiments/{experiment_id}/run")
def enqueue_run_experiment(experiment_id: int, admin=Depends(get_current_admin)):
    q = CommandQueue()
    q.ensure_table()
    cmd_id = q.add_command(f"run experiment {experiment_id}")
    return {"command_id": cmd_id, "status": "PENDING"}


@router.get("/learning/reflections")
def list_reflections(limit: int = 50, admin=Depends(get_current_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, cycle_id, primary_goal, input_objective, execution_result, success, confidence_before, confidence_after, created_at
            FROM reflections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    return {"reflections": [dict(r) for r in rows]}


# -------------------------------------------------
# NOVA DASHBOARD
# -------------------------------------------------

@router.get("/nova/dashboard")
def nova_dashboard(admin=Depends(get_current_admin)):

    nova = Nova()
    system_status = nova.status()

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute("SELECT * FROM economic_experiments")
        experiments = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM agents")
        agents = [dict(row) for row in cursor.fetchall()]

    return {
        "system": system_status,
        "experiments": experiments,
        "agents": agents
    }
