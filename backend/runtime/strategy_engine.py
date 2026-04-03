from backend.database import get_db


class StrategyEngine:

    # ----------------------------------
    # FETCH PENDING PROPOSALS
    # ----------------------------------

    def fetch_pending_proposals(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id,
                   niche_name,
                   cash_score,
                   proposed_budget
            FROM market_proposals
            WHERE status='PENDING'
            ORDER BY cash_score DESC
            """)

            rows = cursor.fetchall()

        proposals = []

        for r in rows:

            proposals.append({
                "id": r["id"],
                "niche": r["niche_name"],
                "cash_score": r["cash_score"],
                "budget": r["proposed_budget"]
            })

        return proposals

    # ----------------------------------
    # CREATE EXPERIMENT FROM PROPOSAL
    # ----------------------------------

    def create_experiment(self, proposal):

        name = f"experiment_{proposal['niche']}"

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO economic_experiments
            (name, experiment_type, capital_allocated, status)
            VALUES (?, 'MARKET_TEST', ?, 'IDEA')
            """, (
                name,
                proposal["budget"]
            ))

            experiment_id = cursor.lastrowid

            cursor.execute("""
            UPDATE market_proposals
            SET status='APPROVED'
            WHERE id=?
            """, (proposal["id"],))

            conn.commit()

        return experiment_id