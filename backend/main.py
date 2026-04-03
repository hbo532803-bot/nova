import time
from datetime import datetime
from pathlib import Path

from backend.runtime.cognitive_loop import CognitiveLoop
from backend.execution.hardened_executor import hardened_execute


MARKET_GUARD_FILE = Path("backend/memory/market_last_run.txt")


# ---------------------------------------------------
# ENTRY GATE
# ---------------------------------------------------

def entry_gate(plan: dict):
    """
    🚪 ENTRY GATE
    Final execution safety check
    """

    required_fields = [
        "assumed_failure",
        "failure_impact",
        "confidence_score"
    ]

    for field in required_fields:
        if field not in plan:
            raise RuntimeError(f"ENTRY GATE BLOCKED: missing '{field}'")

    confidence = plan["confidence_score"]

    if confidence < 50:
        raise RuntimeError("ENTRY GATE BLOCKED: confidence < 50 (planning only)")

    if 50 <= confidence < 70:
        raise RuntimeError(
            "ENTRY GATE BLOCKED: confidence 50–70 requires human permission"
        )

    plan.setdefault("_permission_context", {
        "session": "default",
        "source": "entry_gate"
    })

    return hardened_execute(plan)


# ---------------------------------------------------
# DAILY MARKET GUARD
# ---------------------------------------------------

def should_run_market_scan():

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if not MARKET_GUARD_FILE.exists():
        MARKET_GUARD_FILE.write_text(today)
        return True

    last_run = MARKET_GUARD_FILE.read_text().strip()

    if last_run != today:
        MARKET_GUARD_FILE.write_text(today)
        return True

    return False


# ---------------------------------------------------
# MAIN RUNTIME
# ---------------------------------------------------

def start_nova():

    loop = CognitiveLoop()

    print("🚀 Nova runtime started")

    while True:

        try:

            # -----------------------------
            # MARKET SCAN (ONCE PER DAY)
            # -----------------------------

            if should_run_market_scan():
                print("📊 Running daily market scan")
                loop.market.run_full_weekly_cycle()

            # -----------------------------
            # COGNITIVE CYCLE
            # -----------------------------

            loop.run_cycle()

        except Exception as e:

            print("⚠ Runtime error:", str(e))

        time.sleep(30)


# ---------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------

if __name__ == "__main__":

    start_nova()