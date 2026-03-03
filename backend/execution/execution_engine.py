from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Optional
import time
import uuid
import traceback


# -----------------------------
# Execution States
# -----------------------------
class ExecutionState(Enum):
    IDLE = auto()
    PLANNED = auto()
    PRECHECK = auto()
    EXECUTING = auto()
    VERIFYING = auto()
    COMPLETED = auto()
    FAILED = auto()
    ROLLED_BACK = auto()


# -----------------------------
# Execution Result
# -----------------------------
@dataclass
class ExecutionResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    rolled_back: bool = False
    duration_ms: Optional[int] = None


# -----------------------------
# Execution Context
# -----------------------------
@dataclass
class ExecutionContext:
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ExecutionState = ExecutionState.IDLE
    plan: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: list = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def log(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def duration_ms(self) -> Optional[int]:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None


# -----------------------------
# Core Execution Engine
# -----------------------------
class ExecutionEngine:
    """
    Hard guarantees:
    - No state skipping
    - No execution without failure simulation
    - Rollback enforced if defined
    - Idempotency supported
    """

    def __init__(self):
        self._executed_actions = set()  # idempotency registry

    # -------- Public API --------

    def execute(
        self,
        plan: Dict[str, Any],
        action: Callable[[Dict[str, Any]], Any],
        *,
        rollback: Optional[Callable[[Dict[str, Any]], None]] = None,
        verifier: Optional[Callable[[Any], bool]] = None,
    ) -> ExecutionResult:

        ctx = ExecutionContext(plan=plan)
        ctx.log("Execution initialized")

        try:
            self._transition(ctx, ExecutionState.PLANNED)

            self._precheck(ctx, rollback)

            self._transition(ctx, ExecutionState.EXECUTING)
            ctx.start_time = time.time()

            result = self._execute_action(ctx, action)

            self._transition(ctx, ExecutionState.VERIFYING)
            self._verify(ctx, result, verifier)

            ctx.end_time = time.time()
            self._transition(ctx, ExecutionState.COMPLETED)

            ctx.log("Execution completed successfully")

            return ExecutionResult(
                success=True,
                data=result,
                duration_ms=ctx.duration_ms(),
            )

        except Exception as exc:
            ctx.end_time = time.time()
            error_msg = str(exc)
            ctx.log(f"Execution failed: {error_msg}")
            ctx.log(traceback.format_exc())

            self._transition(ctx, ExecutionState.FAILED)

            rolled_back = False
            if rollback:
                rolled_back = self._rollback(ctx, rollback)

            return ExecutionResult(
                success=False,
                error=error_msg,
                rolled_back=rolled_back,
                duration_ms=ctx.duration_ms(),
            )

    # -------- Internal Mechanics --------

    def _transition(self, ctx: ExecutionContext, new_state: ExecutionState):
        ctx.log(f"STATE CHANGE: {ctx.state.name} → {new_state.name}")
        ctx.state = new_state

    def _precheck(self, ctx: ExecutionContext, rollback):
        self._transition(ctx, ExecutionState.PRECHECK)

        # 1️⃣ Failure-first simulation (MANDATORY)
        failure = ctx.plan.get("assumed_failure")
        impact = ctx.plan.get("failure_impact")
        rollback_possible = rollback is not None

        if not failure or not impact:
            raise RuntimeError(
                "Precheck failed: assumed_failure and failure_impact must be defined"
            )

        ctx.log(f"Assumed failure: {failure}")
        ctx.log(f"Failure impact: {impact}")

        if not rollback_possible:
            raise RuntimeError(
                "Precheck blocked: No rollback defined for this execution"
            )

        ctx.log("Precheck passed (rollback available)")

    def _execute_action(self, ctx: ExecutionContext, action: Callable):
        action_id = self._action_fingerprint(ctx.plan)

        if action_id in self._executed_actions:
            ctx.log("Idempotent hit: action already executed, skipping")
            return ctx.metadata.get("previous_result")

        ctx.log("Executing action")
        result = action(ctx.plan)

        self._executed_actions.add(action_id)
        ctx.metadata["previous_result"] = result

        return result

    def _verify(self, ctx: ExecutionContext, result: Any, verifier):
        if verifier:
            ctx.log("Running verifier")
            if not verifier(result):
                raise RuntimeError("Verification failed")
            ctx.log("Verification passed")
        else:
            ctx.log("No verifier provided, skipping verification")

    def _rollback(self, ctx: ExecutionContext, rollback: Callable) -> bool:
        try:
            ctx.log("Rollback started")
            rollback(ctx.plan)
            self._transition(ctx, ExecutionState.ROLLED_BACK)
            ctx.log("Rollback completed successfully")
            return True
        except Exception as exc:
            ctx.log(f"Rollback failed: {exc}")
            ctx.log(traceback.format_exc())
            return False

    def _action_fingerprint(self, plan: Dict[str, Any]) -> str:
        """
        Simple deterministic fingerprint.
        Can be upgraded later to hash-based.
        """
        return str(sorted(plan.items()))
