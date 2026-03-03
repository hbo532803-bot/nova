from database import get_db

with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM market_niches WHERE id = ?", (3,))
    cursor.execute("DELETE FROM market_signals WHERE id = ?", (3,))
    cursor.execute("DELETE FROM market_proposals WHERE id = ?", (3,))
    print("done")
    conn.commit()