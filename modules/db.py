"""
SQLite database for show history and weekly plans.

Tables:
- history: tracks what was used in past shows (dedup source)
- weekly_plan: stores planned content (consumed by daily runner)

Database: data/reflections.db (auto-created)
"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reflections.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_date TEXT NOT NULL UNIQUE,
            pillars TEXT NOT NULL,
            quote TEXT,
            quote_source TEXT,
            deep_dive_topic TEXT,
            talking_points TEXT,
            script_path TEXT,
            audio_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS weekly_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            day_date TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            pillars TEXT NOT NULL,
            deep_dive_topic TEXT NOT NULL,
            quote TEXT NOT NULL,
            quote_source TEXT,
            talking_points TEXT NOT NULL,
            theme_connection TEXT,
            status TEXT DEFAULT 'planned',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(week_start, day_date)
        );
    """)
    conn.commit()
    conn.close()


def get_history(days=90):
    """Return last N days of show history as list of dicts."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM history ORDER BY show_date DESC LIMIT ?", (days,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        # Parse JSON fields
        for field in ("pillars", "talking_points"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(d)
    return results


def save_history(show_date, pillars, quote, quote_source=None,
                 deep_dive_topic=None, talking_points=None,
                 script_path=None, audio_path=None):
    """Save a show's metadata to the history table."""
    conn = _connect()
    pillars_json = json.dumps(pillars) if isinstance(pillars, list) else pillars
    tp_json = json.dumps(talking_points) if isinstance(talking_points, list) else talking_points
    conn.execute(
        """INSERT OR REPLACE INTO history
           (show_date, pillars, quote, quote_source, deep_dive_topic,
            talking_points, script_path, audio_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (show_date, pillars_json, quote, quote_source, deep_dive_topic,
         tp_json, script_path, audio_path)
    )
    conn.commit()
    conn.close()


def save_weekly_plan(week_start, plans):
    """Save a list of daily plan dicts to the weekly_plan table."""
    conn = _connect()
    for plan in plans:
        pillars_json = json.dumps(plan["pillars"]) if isinstance(plan["pillars"], list) else plan["pillars"]
        tp_json = json.dumps(plan["talking_points"]) if isinstance(plan["talking_points"], list) else plan["talking_points"]
        conn.execute(
            """INSERT OR REPLACE INTO weekly_plan
               (week_start, day_date, day_of_week, pillars, deep_dive_topic,
                quote, quote_source, talking_points, theme_connection, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned')""",
            (week_start, plan["day_date"], plan["day_of_week"],
             pillars_json, plan["deep_dive_topic"],
             plan["quote"], plan.get("quote_source"),
             tp_json, plan.get("theme_connection"))
        )
    conn.commit()
    conn.close()


def get_plan_for_date(date_str):
    """Get the plan for a specific date. Returns dict or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM weekly_plan WHERE day_date = ? ORDER BY id DESC LIMIT 1",
        (date_str,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field in ("pillars", "talking_points"):
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def mark_plan_generated(date_str):
    """Mark a plan as generated (script was produced from it)."""
    conn = _connect()
    conn.execute(
        "UPDATE weekly_plan SET status = 'generated' WHERE day_date = ?",
        (date_str,)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {os.path.abspath(DB_PATH)}")
