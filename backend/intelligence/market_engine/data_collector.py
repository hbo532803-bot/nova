import datetime
import requests
from bs4 import BeautifulSoup
import re
import time
from backend.database import get_db


class MarketDataCollector:

    def __init__(self):
        self.week_tag = self._current_week()

    def _current_week(self):
        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    # -------------------------------------------------
    # ENSURE TABLE EXISTS
    # -------------------------------------------------

    def ensure_table(self):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_name TEXT,
                    source TEXT,
                    signal_type TEXT,
                    value REAL,
                    week_tag TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # -------------------------------------------------
    # REAL UPWORK CONNECTOR
    # -------------------------------------------------

    def collect_upwork_signal(self, niche):

        try:
            query = niche.replace(" ", "%20")
            url = f"https://www.upwork.com/nx/search/jobs/?q={query}"

            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"job_posts": 0, "avg_budget": 0, "urgent_flag": 0}

            soup = BeautifulSoup(response.text, "html.parser")
            text_blob = soup.get_text().lower()

            job_sections = soup.find_all("section")
            job_count = len(job_sections)

            budgets = []
            for match in re.findall(r"\$([0-9,]+)", text_blob):
                try:
                    budgets.append(int(match.replace(",", "")))
                except:
                    continue

            avg_budget = sum(budgets) / len(budgets) if budgets else 0
            urgent_flag = 1 if any(word in text_blob for word in ["urgent", "immediately", "asap"]) else 0

            time.sleep(2)

            return {
                "job_posts": job_count,
                "avg_budget": avg_budget,
                "urgent_flag": urgent_flag
            }

        except Exception as e:
            print("Upwork error:", e)
            return {"job_posts": 0, "avg_budget": 0, "urgent_flag": 0}

    # -------------------------------------------------
    # GOOGLE TRENDS CONNECTOR
    # -------------------------------------------------

    def collect_trend_signal(self, niche):

        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl='en-US', tz=330)
            pytrends.build_payload([niche], timeframe='today 3-m')
            data = pytrends.interest_over_time()

            if data.empty:
                return {"trend_growth": 0, "spike_score": 0}

            values = data[niche].tolist()

            long_term = sum(values) / len(values)
            short_term = values[-1]

            return {
                "trend_growth": min(100, long_term),
                "spike_score": min(100, short_term)
            }

        except Exception as e:
            print("Trend API error:", e)
            return {"trend_growth": 0, "spike_score": 0}

    # -------------------------------------------------
    # SAFE STORE SIGNAL
    # -------------------------------------------------

    def store_signal(self, niche, source, signal_type, value):

        with get_db() as conn:
            cursor = conn.cursor()

            # Prevent duplicates for same week
            cursor.execute("""
                SELECT id FROM market_signals
                WHERE niche_name = ?
                AND source = ?
                AND signal_type = ?
                AND week_tag = ?
            """, (niche, source, signal_type, self.week_tag))

            if cursor.fetchone():
                return

            cursor.execute("""
                INSERT INTO market_signals
                (niche_name, source, signal_type, value, week_tag)
                VALUES (?, ?, ?, ?, ?)
            """, (niche, source, signal_type, value, self.week_tag))

    # -------------------------------------------------
    # FULL PIPELINE
    # -------------------------------------------------

    def run_collection(self, niches):

        print("📡 Collecting market signals...")

        if not niches:
            print("⚠ No niches provided")
            return

        self.ensure_table()

        for niche in niches:

            upwork = self.collect_upwork_signal(niche)
            trend = self.collect_trend_signal(niche)

            self.store_signal(niche, "upwork", "job_posts", upwork["job_posts"])
            self.store_signal(niche, "upwork", "avg_budget", upwork["avg_budget"])
            self.store_signal(niche, "upwork", "urgent_flag", upwork["urgent_flag"])

            self.store_signal(niche, "google_trends", "trend_growth", trend["trend_growth"])
            self.store_signal(niche, "google_trends", "spike_score", trend["spike_score"])

        print("✅ Signal collection complete")