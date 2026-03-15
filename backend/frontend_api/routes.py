from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict
import uuid
from datetime import datetime, timedelta

from backend.frontend_api.event_bus import broadcast
from backend.frontend_api.events import log_event

from backend.memory.goal_memory import remember, list_goals, primary_goal
from backend.memory.reflection_memory import ReflectionMemory

from backend.intelligence.ethics_gate import check
from backend.intelligence.llm_engine import run_llm_reasoning
from backend.intelligence.decision_router import route_decision
from backend.intelligence.planning_brain import brain
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.self_analyzer import SelfAnalyzer
from backend.intelligence.suggestion_executor import SuggestionExecutor

from backend.intelligence.strategic_planner import StrategicPlanner
from backend.intelligence.plan_executor import PlanExecutor
from backend.intelligence.experiment_engine import EconomicEngine
from backend.intelligence.blueprint_engine import BlueprintEngine
from backend.intelligence.agent_orchestrator import AgentOrchestrator
from backend.intelligence.economic_controller import EconomicController

from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from backend.intelligence.market_engine.threshold_advisor import ThresholdAdvisor

from backend.system.permission_gate import permission_gate
from backend.system.kill_switch import kill_switch

from backend.tools.diff_engine import apply_change
from backend.tools.rollback_manager import rollback_last

from backend.auth import authenticate_user, create_access_token, get_current_admin

from backend.database import get_db

from backend.core.nova_core import nova_core
from backend.nova import Nova

router = APIRouter()

STATE = {"status": "IDLE"}
PENDING_DIFF = {}

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

@router.get("/api/status")
def get_status():

    engine = ConfidenceEngine()

    return {
        "status": "running",
        "confidence": engine.get_score()
    }


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

@router.get("/api/system/self-analysis")
def system_self_analysis(admin=Depends(get_current_admin)):

    analyzer = SelfAnalyzer()
    return analyzer.generate_system_report()


# -------------------------------------------------
# SYSTEM PAUSE
# -------------------------------------------------

@router.post("/system/pause")
def pause_system(admin=Depends(get_current_admin)):

    kill_switch.trigger()

    return {"status": "paused"}


# -------------------------------------------------
# SYSTEM RESUME
# -------------------------------------------------

@router.post("/system/resume")
def resume_system(admin=Depends(get_current_admin)):

    kill_switch.reset()

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

    result = nova_core.handle_command(goal)

    broadcast({
        "type": "log",
        "level": "info",
        "message": "NovaCore execution finished"
    })

    return result


# -------------------------------------------------
# ROLLBACK
# -------------------------------------------------

@router.post("/rollback/last")
def rollback(path: str, admin=Depends(get_current_admin)):

    rollback_last(path)

    broadcast({
        "type": "log",
        "level": "warn",
        "message": f"Rollback performed on {path}"
    })

    return {"ok": True}


# -------------------------------------------------
# ECONOMIC
# -------------------------------------------------

@router.get("/economic/run")
def run_economic_cycle(admin=Depends(get_current_admin)):

    engine = EconomicEngine()
    return engine.run_cycle()


@router.get("/economic/blueprint")
def generate_blueprint(admin=Depends(get_current_admin)):

    engine = BlueprintEngine()
    return engine.run_cycle()


@router.post("/economic/orchestrate")
def run_orchestrator(data: dict, admin=Depends(get_current_admin)):

    idea = data.get("idea")

    if not idea:
        return {"error": "Idea required"}

    orchestrator = AgentOrchestrator()
    return orchestrator.orchestrate(idea)


# -------------------------------------------------
# MARKET
# -------------------------------------------------

@router.post("/market/run-weekly")
def run_weekly_market_scan(background_tasks: BackgroundTasks, admin=Depends(get_current_admin)):

    runner = MarketWeeklyRunner()
    background_tasks.add_task(runner.run_full_weekly_cycle)

    return {"status": "started"}


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


# -------------------------------------------------
# FULL NOVA CYCLE
# -------------------------------------------------

@router.post("/nova/run-full-cycle")
def run_full_cycle(admin=Depends(get_current_admin)):

    orchestrator = AgentOrchestrator()
    return orchestrator.run_full_system_cycle()



@router.post("/nova/opportunity/{id}/execute")
def execute_opportunity(id:int):

    return {"status":"execution_started","id":id}    

@router.post("/nova/opportunity/discover")
def discover():

    # run opportunity scanner

    return {"status":"scan_started"}  

@router.get("/nova/agents")
def get_agents():

    return [
        {
            "id":1,
            "name":"Agent Alpha",
            "status":"running"
        },
        {
            "id":2,
            "name":"Agent Beta",
            "status":"idle"
        }
    ]  

@router.get("/nova/opportunities")
def get_opportunities():

    return [
        {
            "id": 1,
            "title": "Market Arbitrage",
            "description": "Price difference detected between exchanges"
        },
        {
            "id": 2,
            "title": "Automation Opportunity",
            "description": "Process automation detected"
        }
    ]


@router.get("/nova/execution")
def get_execution_pipeline():

    return [
        {
            "id": 1,
            "name": "Opportunity Execution",
            "status": "running"
        },
        {
            "id": 2,
            "name": "Experiment Task",
            "status": "pending"
        }
    ]   


@router.get("/nova/logs")
def get_logs():

    return [
        {
            "message": "Nova system started"
        },
        {
            "message": "Agent Alpha executed task"
        }
    ]     