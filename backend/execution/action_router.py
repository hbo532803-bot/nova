from __future__ import annotations

from typing import Any, Dict, Optional

from backend.frontend_api.event_bus import broadcast
from backend.execution.action_types import ActionType
from backend.system.state_store import StateStore
from backend.memory.reflection_memory import ReflectionMemory
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.opportunity_engine import OpportunityEngine
from backend.intelligence.economic_attack_engine import EconomicAttackEngine
from backend.intelligence.experiment_runner import ExperimentRunner
from backend.runtime.agent_manager import AgentManager
from backend.database import get_db
import json
from backend.intelligence.strategy_learning import StrategyLearningEngine
from backend.system.stability import SystemStability
from backend.intelligence.experiment_lifecycle import ExperimentLifecycleEngine
from backend.knowledge.graph_store import KnowledgeGraphStore
from backend.intelligence.research_engine import ResearchEngine
from backend.runtime.agent_factory import AgentFactory
from backend.intelligence.traffic_engine import TrafficEngine
from backend.intelligence.revenue_execution_engine import RevenueExecutionEngine
from backend.intelligence.lead_interaction_engine import LeadInteractionEngine
from backend.intelligence.offer_conversion_engine import OfferConversionEngine
from backend.intelligence.market_intelligence_engine import MarketIntelligenceEngine
from backend.intelligence.admin_command_engine import AdminCommandEngine
from backend.intelligence.communication_control_engine import CommunicationControlEngine


class ActionRouter:
    """
    Single action routing surface for Nova.
    No subsystem should perform real work outside these action handlers.
    """

    def __init__(self):
        self.state_store = StateStore()
        self.reflection = ReflectionMemory()
        self.confidence = ConfidenceEngine()
        self.opportunities = OpportunityEngine()
        self.econ_attack = EconomicAttackEngine()
        self.experiment_runner = ExperimentRunner()
        self.agent_manager = AgentManager()
        self.strategy = StrategyLearningEngine()
        self.stability = SystemStability()
        self.lifecycle = ExperimentLifecycleEngine()
        self.kg = KnowledgeGraphStore()
        self.research = ResearchEngine()
        self.agent_factory = AgentFactory()
        self.traffic = TrafficEngine()
        self.revenue_execution = RevenueExecutionEngine()
        self.leads = LeadInteractionEngine()
        self.offer_conversion = OfferConversionEngine()
        self.market_intelligence = MarketIntelligenceEngine()
        self.admin_commands = AdminCommandEngine()
        self.communication = CommunicationControlEngine()

    def run(self, action: Dict[str, Any], plan: Dict[str, Any]) -> Any:
        action_type = ActionType(str(action.get("type")))
        payload = action.get("payload") or {}

        broadcast({"type": "log", "level": "info", "message": f"ActionRouter executing {action_type}"})

        if action_type == ActionType.STATE_TRANSITION:
            target = str(payload.get("state"))
            snap = self.state_store.set(target)  # type: ignore[arg-type]
            return {"state": snap.state, "updated_at": snap.updated_at}

        if action_type == ActionType.MARKET_SCAN:
            return self.opportunities.run_discovery()

        if action_type == ActionType.OPPORTUNITY_DISCOVER:
            return self.opportunities.run_discovery()

        if action_type == ActionType.OPPORTUNITY_APPROVE:
            proposal_id = int(payload.get("proposal_id"))
            return self.opportunities.approve_proposal(proposal_id)

        if action_type == ActionType.OPPORTUNITY_REJECT:
            proposal_id = int(payload.get("proposal_id"))
            return self.opportunities.reject_proposal(proposal_id)

        if action_type == ActionType.OPPORTUNITY_CONVERT:
            proposal_id = int(payload.get("proposal_id"))
            return self.opportunities.convert_to_experiment(proposal_id)

        if action_type == ActionType.EXPERIMENT_CREATE:
            # Launch experiments from proposals inside the economic engine policy.
            return self.econ_attack.run_cycle()

        if action_type == ActionType.EXPERIMENT_RUN:
            exp_id = int(payload.get("experiment_id"))
            return self.experiment_runner.run(exp_id)

        if action_type == ActionType.AGENT_HIBERNATE:
            agent_id = int(payload.get("agent_id"))
            self.agent_manager.hibernate_agent(agent_id)
            return {"agent_id": agent_id, "status": "HIBERNATED"}

        if action_type == ActionType.AGENT_WAKE:
            agent_id = int(payload.get("agent_id"))
            self.agent_manager.wake_agent(agent_id)
            return {"agent_id": agent_id, "status": "ACTIVE"}

        if action_type == ActionType.REFLECTION_RECORD:
            data = payload.get("reflection") or {}
            self.reflection.record_reflection(data)
            # Confidence adjustment is driven by outcomes.
            if data.get("success"):
                self.confidence.adjust(+1)
            else:
                self.confidence.adjust(-1)
            return {"recorded": True}

        if action_type == ActionType.PLAYBOOK_ATTACH:
            experiment_id = int(payload.get("experiment_id"))
            playbook_name = str(payload.get("playbook_name"))
            playbook = payload.get("playbook")
            if not isinstance(playbook, dict):
                raise RuntimeError("PLAYBOOK_ATTACH missing playbook dict")
            key = f"experiment_playbook_{experiment_id}"
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                    (key, json.dumps(playbook)),
                )
                conn.commit()
            return {"experiment_id": experiment_id, "playbook_name": playbook_name, "attached": True}

        if action_type == ActionType.STRATEGY_LEARN:
            lookback = int(payload.get("lookback") or 100)
            return self.strategy.learn(lookback=lookback)

        if action_type == ActionType.HEALTH_CHECK:
            return self.stability.health()

        if action_type == ActionType.RECOVER_SYSTEM:
            return self.stability.recover()

        if action_type == ActionType.EXPERIMENT_EVALUATE_PORTFOLIO:
            limit = int(payload.get("limit") or 50)
            return self.lifecycle.evaluate_portfolio(limit=limit)

        if action_type == ActionType.EXPERIMENT_APPLY_LIFECYCLE:
            decisions = payload.get("decisions") or []
            if not isinstance(decisions, list):
                raise RuntimeError("EXPERIMENT_APPLY_LIFECYCLE requires decisions list")
            return self.lifecycle.apply_decisions(decisions)

        if action_type == ActionType.KG_UPSERT_NODE:
            node_type = str(payload.get("node_type"))
            node_key = str(payload.get("node_key"))
            data = payload.get("data") or {}
            if not isinstance(data, dict):
                raise RuntimeError("KG_UPSERT_NODE requires data dict")
            return self.kg.upsert_node(node_type, node_key, data)

        if action_type == ActionType.KG_ADD_EDGE:
            return self.kg.add_edge(
                str(payload.get("source_type")),
                str(payload.get("source_key")),
                str(payload.get("relation")),
                str(payload.get("target_type")),
                str(payload.get("target_key")),
                weight=float(payload.get("weight") or 1.0),
            )

        if action_type == ActionType.RESEARCH_RUN:
            max_proposals = int(payload.get("max_proposals") or 5)
            return self.research.run(max_proposals=max_proposals)

        if action_type == ActionType.AGENT_FACTORY_CREATE:
            required = payload.get("required_capabilities") or []
            if not isinstance(required, list):
                raise RuntimeError("AGENT_FACTORY_CREATE requires required_capabilities list")
            mission_id = str(payload.get("mission_id") or plan.get("mission_id") or "")
            return self.agent_factory.create_spec(required_capabilities=[str(x) for x in required], mission_id=mission_id)

        if action_type == ActionType.AGENT_FACTORY_EVOLVE:
            return self.agent_factory.evolve_specs()

        if action_type == ActionType.TRAFFIC_GENERATE:
            return self.traffic.generate_traffic(
                mission_id=str(payload.get("mission_id") or plan.get("mission_id") or ""),
                channel=str(payload.get("channel") or "content_posts"),
                volume=int(payload.get("volume") or 0),
                quality_score=float(payload.get("quality_score") or 0.5),
                experiment_id=(int(payload.get("experiment_id")) if payload.get("experiment_id") is not None else None),
                mode=str(payload.get("mode") or "manual"),
            )

        if action_type == ActionType.EXECUTION_APPLY_PRIORITY:
            return self.revenue_execution.execute_for_experiment(
                int(payload.get("experiment_id")),
                priority_level=str(payload.get("priority_level") or "LOW"),
                decision=str(payload.get("decision") or "hold"),
            )

        if action_type == ActionType.EXECUTION_RUN_PENDING:
            exp = payload.get("experiment_id")
            return self.revenue_execution.run_pending_actions(experiment_id=(int(exp) if exp is not None else None))

        if action_type == ActionType.LEAD_CAPTURE:
            return self.leads.capture_lead(
                mission_id=str(payload.get("mission_id") or ""),
                name=str(payload.get("name") or "unknown"),
                email=str(payload.get("email") or ""),
                phone=str(payload.get("phone") or ""),
                source=str(payload.get("source") or "inbound"),
                metadata=(payload.get("metadata") or {}),
            )

        if action_type == ActionType.LEAD_QUEUE_MESSAGE:
            return self.leads.queue_message_for_approval(
                lead_id=int(payload.get("lead_id")),
                experiment_id=int(payload.get("experiment_id")),
                channel=str(payload.get("channel") or "email"),
                message_body=str(payload.get("message_body") or ""),
            )

        if action_type == ActionType.LEAD_APPROVE_MESSAGE:
            return self.leads.approve_queued_message(
                queue_id=int(payload.get("queue_id")),
                approved_by=str(payload.get("approved_by") or "admin"),
            )

        if action_type == ActionType.CONVERSION_CREATE_OFFER:
            return self.offer_conversion.create_offer_for_lead(
                lead_id=int(payload.get("lead_id")),
                experiment_id=(int(payload.get("experiment_id")) if payload.get("experiment_id") is not None else None),
                service_type=(str(payload.get("service_type")) if payload.get("service_type") else None),
                context=(payload.get("context") or {}),
            )

        if action_type == ActionType.CONVERSION_QUEUE_RESPONSE:
            return self.offer_conversion.queue_offer_response_for_approval(
                attempt_id=int(payload.get("attempt_id")),
                channel=str(payload.get("channel") or "email"),
            )

        if action_type == ActionType.CONVERSION_MARK_PAYMENT:
            return self.offer_conversion.mark_real_payment(
                attempt_id=int(payload.get("attempt_id")),
                amount=float(payload.get("amount") or 0),
                approved_by=str(payload.get("approved_by") or "system"),
            )

        if action_type == ActionType.CONVERSION_FEEDBACK:
            return self.offer_conversion.conversion_feedback(limit=int(payload.get("limit") or 20))

        if action_type == ActionType.MARKET_INTELLIGENCE_INGEST:
            return self.market_intelligence.ingest_signal(
                platform=str(payload.get("platform") or "linkedin"),
                content=str(payload.get("content") or ""),
                source_url=str(payload.get("source_url") or ""),
                author_handle=str(payload.get("author_handle") or ""),
                is_simulated=bool(payload.get("is_simulated") or False),
            )

        if action_type == ActionType.MARKET_INTELLIGENCE_SCAN:
            return self.market_intelligence.discover_opportunities(
                limit=int(payload.get("limit") or 25),
                real_only=bool(payload.get("real_only", True)),
            )

        if action_type == ActionType.ADMIN_COMMAND_PARSE:
            return self.admin_commands.parse_command(
                command_text=str(payload.get("command_text") or plan.get("goal") or ""),
                admin_user=str(payload.get("admin_user") or "admin"),
            )

        if action_type == ActionType.ADMIN_COMMAND_CREATE_MISSION:
            return self.admin_commands.create_mission_from_command(command_id=int(payload.get("command_id")))

        if action_type == ActionType.COMMUNICATION_SUGGEST_REPLY:
            return self.communication.suggest_reply(
                lead_id=int(payload.get("lead_id")),
                experiment_id=int(payload.get("experiment_id") or 0),
                channel=str(payload.get("channel") or "email"),
                user_message=str(payload.get("user_message") or ""),
                context=(payload.get("context") or {}),
            )

        raise RuntimeError(f"Unknown action type: {action_type}")
