import sqlite3
import uuid
from datetime import datetime, timedelta


class DataService:
    def __init__(self, db_path, DISTANCE_THRESHOLD):
        self.similarity_threshold = 1 - DISTANCE_THRESHOLD
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS articles (id TEXT PRIMARY KEY, title TEXT, date TEXT)'
        )
        self.conn.commit()

    def _jaccard(self, a, b):
        ta, tb = set(a.lower().split()), set(b.lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def is_new_article(self, title):
        try:
            for (stored,) in self.conn.execute('SELECT title FROM articles'):
                if self._jaccard(title, stored) >= self.similarity_threshold:
                    return False
            return True
        except Exception as e:
            print(f"Error checking for new article: {e}")
            return True

    def save_article(self, title, date_time):
        try:
            self.conn.execute('INSERT INTO articles VALUES (?, ?, ?)',
                              (str(uuid.uuid4()), title, date_time.isoformat()))
            self.conn.commit()
            print(f"Article '{title}' saved to database.")
        except Exception as e:
            print(f"Error saving article '{title}': {e}")

    def cleanup_old_articles(self, max_age_days=10):
        try:
            cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
            cur = self.conn.execute('DELETE FROM articles WHERE date < ?', (cutoff,))
            self.conn.commit()
            print(f"Deleted {cur.rowcount} old articles from the database.")
        except Exception as e:
            print(f"Error cleaning up old articles: {e}")
