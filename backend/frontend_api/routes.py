from fastapi import APIRouter, BackgroundTasks
from typing import Dict

from backend.frontend_api.event_bus import broadcast
from backend.frontend_api.events import log_event

from backend.memory.goal_memory import remember, list_goals, primary_goal
from backend.intelligence.ethics_gate import check
from backend.intelligence.llm_engine import run_llm_reasoning
from backend.intelligence.decision_router import route_decision
from backend.intelligence.planning_brain import brain
from backend.intelligence.confidence_engine import ConfidenceEngine
from fastapi import HTTPException
from backend.intelligence.self_analyzer import SelfAnalyzer
from backend.intelligence.suggestion_executor import SuggestionExecutor
from backend.system.permission_gate import permission_gate

from backend.tools.diff_engine import apply_change
from backend.tools.rollback_manager import rollback_last
from backend.memory.reflection_memory import ReflectionMemory
import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.auth import authenticate_user, create_access_token, get_current_admin
from datetime import timedelta
from backend.database import get_db
from datetime import datetime
from backend.intelligence.strategic_planner import StrategicPlanner
from backend.intelligence.plan_executor import PlanExecutor
from backend.intelligence.experiment_engine import EconomicEngine
from backend.intelligence.blueprint_engine import BlueprintEngine
from backend.intelligence.agent_orchestrator import AgentOrchestrator
from backend.intelligence.economic_controller import EconomicController
from backend.nova import Nova
from fastapi import APIRouter, Depends
from backend.auth import get_current_admin
from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from fastapi import BackgroundTasks
from backend.system.kill_switch import kill_switch
from backend.intelligence.agent_orchestrator import AgentOrchestrator




router = APIRouter()

STATE = {"status": "IDLE"}
PENDING_DIFF = {}


# -------------------------
# Utility
# -------------------------

def reset_run_state():
    permission_gate.reset()
    PENDING_DIFF.clear()


# -------------------------
# Status
# -------------------------

def record_cycle(goal, decision, outcome, success):
    try:
        reflection = ReflectionMemory()

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

            "confidence_before": ConfidenceEngine.score,
            "confidence_after": ConfidenceEngine.score,
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


@router.get("/api/status")
def get_status():

    engine = ConfidenceEngine()

    return {
        "status": "running",
        "confidence": engine.get_score()
    }

# -------------------------
# Memory
# -------------------------

@router.get("/memory/goals")
def get_goals():
    return list_goals()


# -------------------------
# Run
# -------------------------

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

    # ----------------------------
    # STRATEGIC PLANNING
    # ----------------------------

    planner = StrategicPlanner()
    executor = PlanExecutor()

    broadcast({
        "type": "log",
        "level": "think",
        "message": "Starting strategic decomposition"
    })

    plan = planner.decompose_goal(goal)

    broadcast({
        "type": "log",
        "level": "info",
        "message": "Plan created. Executing steps"
    })

    executor.execute_plan(goal, plan)

    broadcast({
        "type": "log",
        "level": "info",
        "message": "Run finished"
    })

    return {
        "status": "completed",
        "steps": plan.get("steps", [])
    }



# -------------------------
# Rollback
# -------------------------

@router.post("/rollback/last")
def rollback(path: str, admin=Depends(get_current_admin)):

    result = rollback_last(path)

    broadcast({
        "type": "log",
        "level": "warn",
        "message": f"Rollback performed on {path}"
    })

    ConfidenceEngine.failure()

    return {"ok": True}
@router.get("/system/stats")
def system_stats(admin=Depends(get_current_admin)):

    today = datetime.utcnow().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()

        # API usage
        cursor.execute(
            "SELECT calls, tokens FROM api_usage WHERE date = ?",
            (today,)
        )
        usage = cursor.fetchone()

        calls = usage[0] if usage else 0
        tokens = usage[1] if usage else 0

        # Reflection count
        cursor.execute("SELECT COUNT(*) FROM reflections")
        reflection_count = cursor.fetchone()[0]

        # Confidence
        cursor.execute("SELECT score, autonomy FROM confidence_state WHERE id=1")
        conf = cursor.fetchone()
        confidence_score = conf[0] if conf else 0
        autonomy = conf[1] if conf else "UNKNOWN"

    return {
        "api_calls_today": calls,
        "tokens_today": tokens,
        "reflection_entries": reflection_count,
        "confidence_score": confidence_score,
        "autonomy_mode": autonomy
    }


@router.get("/system/self-analysis")
def system_self_analysis(admin=Depends(get_current_admin)):
    analyzer = SelfAnalyzer()
    return analyzer.generate_system_report()


@router.post("/system/apply-suggestions")
def apply_suggestions(request: dict, admin=Depends(get_current_admin)):

    suggestions = request.get("suggestions", [])

    if not suggestions:
        return {"status": "no_suggestions_provided"}



    executor = SuggestionExecutor()
    applied = executor.apply_suggestions(suggestions)

    return {
        "status": "applied",
        "applied_actions": applied
    }

@router.get("/economic/run")
def run_economic_cycle(admin=Depends(get_current_admin)):

    engine = EconomicEngine()
    result = engine.run_cycle()

    return result

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

#@router.post("/economic/full-cycle")
#def run_full_cycle(admin=Depends(get_current_admin)):

 #   controller = EconomicController()
  #  return controller.run_full_cycle()

@router.post("/economic/advance/{experiment_id}")
def advance_experiment(experiment_id: int):
    controller = EconomicController()
    return controller.advance_lifecycle(experiment_id)




@router.post("/economic/validate/{experiment_id}")
def validate_experiment(experiment_id: int, score: float):
    controller = EconomicController()
    return controller.update_validation(experiment_id, score)


@router.post("/economic/evaluate/{experiment_id}")
def evaluate_experiment(experiment_id: int):
    controller = EconomicController()
    return controller.evaluate_progress(experiment_id)


@router.post("/economic/revenue/{experiment_id}")
def add_revenue(experiment_id: int, revenue: float):
    controller = EconomicController()
    return controller.update_revenue(experiment_id, revenue)



@router.post("/economic/reward-agent/")
def reward_agent(agent_name: str, revenue: float):
    controller = EconomicController()
    return controller.reward_agents(agent_name, revenue)

@router.get("/market/proposals")
def get_market_proposals(admin=Depends(get_current_admin)):

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, niche_name, cash_score, proposed_budget, status
            FROM market_proposals
            ORDER BY cash_score DESC
        """)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

@router.post("/market/proposal/{proposal_id}/approve")
def approve_proposal(proposal_id: int, admin=Depends(get_current_admin)):

    from backend.intelligence.economic_controller import EconomicController

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT niche_name, proposed_budget
            FROM market_proposals
            WHERE id = ?
        """, (proposal_id,))
        row = cursor.fetchone()

        if not row:
            return {"error": "Proposal not found"}

        niche, budget = row

        # Mark approved
        cursor.execute("""
            UPDATE market_proposals
            SET status = 'APPROVED'
            WHERE id = ?
        """, (proposal_id,))

        conn.commit()

    # Spawn controlled experiment
    controller = EconomicController()
    controller.create_experiment_from_market(niche, budget)

    return {"status": "approved", "niche": niche}

@router.post("/market/proposal/{proposal_id}/reject")
def reject_proposal(proposal_id: int, admin=Depends(get_current_admin)):

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE market_proposals
            SET status = 'REJECTED'
            WHERE id = ?
        """, (proposal_id,))

        conn.commit()

    return {"status": "rejected"}


@router.post("/market/run-weekly")
def run_weekly_market_scan(
    background_tasks: BackgroundTasks,
    admin=Depends(get_current_admin)
):
    runner = MarketWeeklyRunner()

    # Background me run karega (UI block nahi hoga)
    background_tasks.add_task(runner.run_full_weekly_cycle)

    return {"status": "started"}

@router.get("/nova/dashboard")
def nova_dashboard(admin=Depends(get_current_admin)):

    nova = Nova()
    system_status = nova.status()

    today = datetime.utcnow().strftime("%Y-%m-%d")

    with get_db() as conn:
        cursor = conn.cursor()

        # Experiments
        cursor.execute("SELECT * FROM economic_experiments")
        experiments = [dict(row) for row in cursor.fetchall()]

        # Agents
        cursor.execute("SELECT * FROM agents")
        agents = [dict(row) for row in cursor.fetchall()]

        # API usage
        cursor.execute(
            "SELECT calls, tokens FROM api_usage WHERE date = ?",
            (today,)
        )
        usage = cursor.fetchone()
        api_calls = usage[0] if usage else 0
        token_usage = usage[1] if usage else 0

        # Reflection count
        cursor.execute("SELECT COUNT(*) FROM reflections")
        reflection_count = cursor.fetchone()[0]

        # Experiment stats
        cursor.execute("SELECT COUNT(*) FROM economic_experiments WHERE status='FAILED'")
        failed_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM economic_experiments WHERE status='SCALING'")
        scaling_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM economic_experiments WHERE status NOT IN ('FAILED','ARCHIVED')")
        active_count = cursor.fetchone()[0]

   

    return {
        "system": system_status,
        "experiments": experiments,
        "agents": agents,
        "risk": {
            "api_calls_today": api_calls,
            "tokens_today": token_usage,
            "reflection_entries": reflection_count,
            "failed_experiments": failed_count,
            "scaling_experiments": scaling_count,
            "active_experiments": active_count,
            "emergency_active": kill_switch.is_triggered()
        }
    }


# =====================================================
# EXPERIMENT INTELLIGENCE SUGGESTIONS
# =====================================================

@router.get("/experiments/suggestions")
def experiment_suggestions(admin=Depends(get_current_admin)):

    from backend.intelligence.experiment_brain import ExperimentBrain

    brain = ExperimentBrain()
    result = brain.analyze_experiments()

    return result


@router.post("/nova/run-full-cycle")
def run_full_cycle(admin=Depends(get_current_admin)):

    

    orchestrator = AgentOrchestrator()
    result = orchestrator.run_full_system_cycle()

    return result

@router.get("/market/threshold-advice")
def threshold_advice(admin=Depends(get_current_admin)):

    from backend.intelligence.market_engine.threshold_advisor import ThresholdAdvisor

    advisor = ThresholdAdvisor()
    return advisor.analyze()