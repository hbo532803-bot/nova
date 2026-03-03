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
        self.week_tag = self._current_week()

    def _current_week(self):
        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    def store_market_memory(self, total_niches, attack_count, avg_cash_score):
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_tag TEXT,
                    total_niches INTEGER,
                    attack_count INTEGER,
                    avg_cash_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                INSERT INTO market_memory
                (week_tag, total_niches, attack_count, avg_cash_score)
                VALUES (?, ?, ?, ?)
            """, (
                self.week_tag,
                total_niches,
                attack_count,
                avg_cash_score
            ))

    def run_full_weekly_cycle(self):

        print("🚀 Starting Weekly Market Intelligence Cycle")

        candidate_niches = self.generator.generate_niches()

        if not candidate_niches:
            print("⚠ No niches generated.")
            return []

        print("🧠 Generated Niches:")
        for n in candidate_niches:
            print("-", n)

        self.collector.run_collection(candidate_niches)
        self.scorer.compute_scores()
        attack_list = self.detector.detect_patterns()
        self.proposal_engine.create_proposals_from_attack_zone(attack_list)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(cash_score) FROM market_niches
                WHERE week_tag = ?
            """, (self.week_tag,))
            avg_cash = cursor.fetchone()[0] or 0

        self.store_market_memory(
            total_niches=len(candidate_niches),
            attack_count=len(attack_list),
            avg_cash_score=round(avg_cash, 2)
        )

        print("🏁 Weekly Cycle Complete")
        return attack_list