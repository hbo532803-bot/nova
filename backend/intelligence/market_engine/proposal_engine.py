import datetime
from backend.database import get_db


class ProposalEngine:

    def __init__(self):

        self.week_tag = self._current_week()

    def _current_week(self):

        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    def create_proposals_from_attack_zone(self, attack_list):

        if not attack_list:

            return []

        created = []

        with get_db() as conn:

            cursor = conn.cursor()

            for niche in attack_list:

                cursor.execute("""
                    SELECT cash_score
                    FROM market_niches
                    WHERE niche_name=? AND week_tag=?
                """, (niche, self.week_tag))

                row = cursor.fetchone()

                if not row:
                    continue

                cash_score = row["cash_score"]

                if cash_score < 35:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM market_proposals
                    WHERE niche_name=? AND week_tag=?
                """, (niche, self.week_tag))

                if cursor.fetchone():
                    continue

                proposed_budget = round(500 + (cash_score * 20), 2)

                cursor.execute("""
                    INSERT INTO market_proposals
                    (niche_name, week_tag, cash_score, proposed_budget, status)
                    VALUES (?, ?, ?, ?, 'PENDING')
                """, (niche, self.week_tag, cash_score, proposed_budget))

                created.append(niche)

            conn.commit()

        return created