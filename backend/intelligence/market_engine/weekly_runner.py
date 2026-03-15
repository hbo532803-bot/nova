import datetime

from backend.database import get_db
from backend.intelligence.market_engine.data_collector import MarketDataCollector
from backend.intelligence.market_engine.scoring_engine import MarketScoringEngine
from backend.intelligence.market_engine.pattern_detector import MarketPatternDetector
from backend.intelligence.market_engine.niche_generator import DynamicNicheGenerator
from backend.intelligence.market_engine.proposal_engine import ProposalEngine


class MarketWeeklyRunner:

    def __init__(self):

        self.collector = MarketDataCollector()
        self.scorer = MarketScoringEngine()
        self.detector = MarketPatternDetector()
        self.generator = DynamicNicheGenerator()
        self.proposal_engine = ProposalEngine()

    # ---------------------------------------
    # Current week
    # ---------------------------------------

    def _current_week(self):

        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    # ---------------------------------------
    # Store weekly memory
    # ---------------------------------------

    def store_market_memory(self, total_niches, attack_count, avg_cash_score):

        week_tag = self._current_week()

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT id
                FROM market_memory
                WHERE week_tag = ?
            """, (week_tag,))

            existing = cursor.fetchone()

            if existing:

                cursor.execute("""
                    UPDATE market_memory
                    SET total_niches=?,
                        attack_count=?,
                        avg_cash_score=?,
                        created_at=CURRENT_TIMESTAMP
                    WHERE week_tag=?
                """, (
                    total_niches,
                    attack_count,
                    avg_cash_score,
                    week_tag
                ))

            else:

                cursor.execute("""
                    INSERT INTO market_memory
                    (week_tag, total_niches, attack_count, avg_cash_score)
                    VALUES (?, ?, ?, ?)
                """, (
                    week_tag,
                    total_niches,
                    attack_count,
                    avg_cash_score
                ))

            conn.commit()

    # ---------------------------------------
    # Weekly pipeline
    # ---------------------------------------

    def run_full_weekly_cycle(self):

        week_tag = self._current_week()

        print("🚀 Starting Weekly Market Intelligence Cycle")

        candidate_niches = self.generator.generate_niches()

        if not candidate_niches:

            print("⚠ No niches generated.")

            return []

        print("🧠 Generated Niches:")

        for n in candidate_niches:

            print("-", n)

        # -----------------------------------
        # Collect signals
        # -----------------------------------

        self.collector.run_collection(candidate_niches)

        # -----------------------------------
        # Reset scoring
        # -----------------------------------

        self.scorer.clear_week()

        # -----------------------------------
        # Score niches
        # -----------------------------------

        self.scorer.compute_scores()

        # -----------------------------------
        # Detect attack zones
        # -----------------------------------

        attack_list = self.detector.detect_patterns()

        print("🎯 Opportunities Detected:", len(attack_list))

        # -----------------------------------
        # Create proposals
        # -----------------------------------

        proposals = self.proposal_engine.create_proposals_from_attack_zone(
            attack_list
        )

        print("💡 Proposals Generated:", len(proposals))

        # -----------------------------------
        # Weekly analytics
        # -----------------------------------

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT AVG(cash_score)
                FROM market_niches
                WHERE week_tag = ?
            """, (week_tag,))

            result = cursor.fetchone()

            if result:

                avg_cash = result[0] if result[0] else 0

            else:

                avg_cash = 0

        # -----------------------------------
        # Store weekly memory
        # -----------------------------------

        self.store_market_memory(
            total_niches=len(candidate_niches),
            attack_count=len(attack_list),
            avg_cash_score=round(avg_cash, 2)
        )

        print("🏁 Weekly Cycle Complete")

        return attack_list