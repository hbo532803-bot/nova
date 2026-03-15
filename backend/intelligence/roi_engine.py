from backend.database import get_db


class ROIEngine:

    def calculate_roi(self, experiment_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT capital_allocated,
                       cost_incurred,
                       revenue_generated
                FROM economic_experiments
                WHERE id=?
                """,
                (experiment_id,)
            )

            row = cursor.fetchone()

            if not row:
                return None

            capital = row["capital_allocated"] or 0
            cost = row["cost_incurred"] or 0
            revenue = row["revenue_generated"] or 0

            if capital == 0:
                return 0

            return (revenue - cost) / capital

    def update_roi(self, experiment_id):

        roi = self.calculate_roi(experiment_id)

        if roi is None:
            return None

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT consecutive_losses
                FROM economic_experiments
                WHERE id=?
                """,
                (experiment_id,)
            )

            row = cursor.fetchone()

            losses = row["consecutive_losses"] if row else 0

            if roi < 0:
                losses += 1
            else:
                losses = 0

            cursor.execute(
                """
                UPDATE economic_experiments
                SET roi=?, consecutive_losses=?
                WHERE id=?
                """,
                (roi, losses, experiment_id)
            )

            conn.commit()

        return {
            "roi": roi,
            "consecutive_losses": losses
        }