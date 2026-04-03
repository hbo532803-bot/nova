import datetime
import requests
from bs4 import BeautifulSoup
import re
import time
from pytrends.request import TrendReq

from backend.database import get_db
from backend.db_retry import run_db_write_with_retry


class MarketDataCollector:

    def __init__(self):

        self.week_tag = self._current_week()

        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }

    # -------------------------------------------------
    # WEEK TAG
    # -------------------------------------------------

    def _current_week(self):

        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    # -------------------------------------------------
    # ENSURE TABLE
    # -------------------------------------------------

    def ensure_table(self):
        # Schema is owned by db_init; keep this for legacy call sites.
        return None

    # -------------------------------------------------
    # STORE SIGNAL
    # -------------------------------------------------

    def store_signal(self, niche, source, signal_type, value):
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM market_signals
                WHERE niche_name=?
                AND source=?
                AND signal_type=?
                AND week_tag=?
                """,
                (niche, source, signal_type, self.week_tag),
            )
            if cursor.fetchone():
                return None
            cursor.execute(
                """
                INSERT INTO market_signals
                (niche_name,source,signal_type,value,week_tag)
                VALUES (?,?,?,?,?)
                """,
                (niche, source, signal_type, value, self.week_tag),
            )
            conn.commit()
            return None

        run_db_write_with_retry("market_signals.upsert", _write)

    # -------------------------------------------------
    # UPWORK SIGNAL
    # -------------------------------------------------

    def collect_upwork_signal(self, niche):

        try:

            query = niche.replace(" ", "%20")

            url = f"https://www.upwork.com/nx/search/jobs/?q={query}"

            r = requests.get(url, headers=self.headers, timeout=10)

            if r.status_code != 200:
                return {"job_posts": 0, "avg_budget": 0}

            soup = BeautifulSoup(r.text, "html.parser")

            job_cards = soup.find_all("article")

            job_count = len(job_cards)

            budgets = []

            for match in re.findall(r"\$([0-9,]+)", soup.get_text()):
                try:
                    budgets.append(int(match.replace(",", "")))
                except:
                    pass

            avg_budget = sum(budgets) / len(budgets) if budgets else 0

            return {
                "job_posts": job_count,
                "avg_budget": avg_budget
            }

        except Exception as e:

            print("Upwork error:", e)

            return {"job_posts": 0, "avg_budget": 0}

    # -------------------------------------------------
    # FIVERR SIGNAL
    # -------------------------------------------------

    def collect_fiverr_signal(self, niche):

        try:

            query = niche.replace(" ", "%20")

            url = f"https://www.fiverr.com/search/gigs?query={query}"

            r = requests.get(url, headers=self.headers, timeout=10)

            if r.status_code != 200:
                return {"gig_count": 0}

            soup = BeautifulSoup(r.text, "html.parser")

            gigs = soup.find_all("article")

            return {"gig_count": len(gigs)}

        except Exception as e:

            print("Fiverr error:", e)

            return {"gig_count": 0}

    # -------------------------------------------------
    # GOOGLE TRENDS
    # -------------------------------------------------

    def collect_trend_signal(self, niche):

        try:

            pytrends = TrendReq(hl="en-US", tz=330)

            pytrends.build_payload([niche], timeframe="today 3-m")

            data = pytrends.interest_over_time()

            if data.empty:
                return {"trend_growth": 0, "spike_score": 0}

            values = data[niche].tolist()

            long_term = sum(values) / len(values)

            short_term = values[-1]

            return {
                "trend_growth": long_term,
                "spike_score": short_term
            }

        except Exception as e:

            print("Trend error:", e)

            return {"trend_growth": 0, "spike_score": 0}

    # -------------------------------------------------
    # REDDIT SIGNAL
    # -------------------------------------------------

    def collect_reddit_signal(self, niche):

        try:

            url = f"https://www.reddit.com/search/?q={niche}"

            r = requests.get(url, headers=self.headers, timeout=10)

            if r.status_code != 200:
                return {"reddit_mentions": 0}

            soup = BeautifulSoup(r.text, "html.parser")

            posts = soup.find_all("h3")

            return {"reddit_mentions": len(posts)}

        except Exception as e:

            print("Reddit error:", e)

            return {"reddit_mentions": 0}

    # -------------------------------------------------
    # GOOGLE COMPETITION
    # -------------------------------------------------

    def collect_competition_signal(self, niche):

        try:

            query = niche.replace(" ", "+")

            url = f"https://www.google.com/search?q={query}"

            r = requests.get(url, headers=self.headers, timeout=10)

            soup = BeautifulSoup(r.text, "html.parser")

            stats = soup.find("div", {"id": "result-stats"})

            if not stats:
                return {"competition_score": 0}

            numbers = re.findall(r"[0-9,]+", stats.text)

            if numbers:
                return {"competition_score": int(numbers[0].replace(",", ""))}

            return {"competition_score": 0}

        except Exception as e:

            print("Competition error:", e)

            return {"competition_score": 0}

    # -------------------------------------------------
    # MAIN COLLECTION PIPELINE
    # -------------------------------------------------

    def run_collection(self, niches):

        print("📡 Collecting market signals...")

        if not niches:
            print("⚠ No niches provided")
            return

        self.ensure_table()

        for niche in niches:

            upwork = self.collect_upwork_signal(niche)
            fiverr = self.collect_fiverr_signal(niche)
            trend = self.collect_trend_signal(niche)
            reddit = self.collect_reddit_signal(niche)
            competition = self.collect_competition_signal(niche)

            self.store_signal(niche, "upwork", "job_posts", upwork["job_posts"])
            self.store_signal(niche, "upwork", "avg_budget", upwork["avg_budget"])

            self.store_signal(niche, "fiverr", "gig_count", fiverr["gig_count"])

            self.store_signal(niche, "google_trends", "trend_growth", trend["trend_growth"])
            self.store_signal(niche, "google_trends", "spike_score", trend["spike_score"])

            self.store_signal(niche, "reddit", "mentions", reddit["reddit_mentions"])

            self.store_signal(niche, "google", "competition_score", competition["competition_score"])

            time.sleep(1)

        print("✅ Signal collection complete")