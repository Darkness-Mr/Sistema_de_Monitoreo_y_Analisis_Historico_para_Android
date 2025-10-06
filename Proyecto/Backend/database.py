import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='monitoring.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            cpu_usage REAL,
            mem_total_kb INTEGER,
            mem_available_kb INTEGER,
            battery_level INTEGER,
            battery_status TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_id INTEGER,
            process_name TEXT,
            pid INTEGER,
            user TEXT,
            FOREIGN KEY(metric_id) REFERENCES system_metrics(id)
        )""")
        conn.commit()
        conn.close()

    def save_metrics(self, metrics: dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # parse memoria
            def _extract_kb(s, default=0):
                try:
                    return int(str(s).split()[0])
                except Exception:
                    return default

            mem_total = _extract_kb(metrics.get("memory_info", {}).get("MemTotal"))
            mem_avail = _extract_kb(metrics.get("memory_info", {}).get("MemAvailable"))
            battery_level = int(metrics.get("battery_info", {}).get("level", 0))
            battery_status = metrics.get("battery_info", {}).get("status", "unknown")

            c.execute(
                "INSERT INTO system_metrics (ts, cpu_usage, mem_total_kb, mem_available_kb, battery_level, battery_status) VALUES (?,?,?,?,?,?)",
                (datetime.utcnow().isoformat(), metrics.get("cpu_usage", 0.0), mem_total, mem_avail, battery_level, battery_status)
            )
            metric_id = c.lastrowid

            for p in metrics.get("processes", []):
                c.execute(
                    "INSERT INTO processes (metric_id, process_name, pid, user) VALUES (?,?,?,?)",
                    (metric_id, p.get("name",""), p.get("pid",-1), p.get("user",""))
                )

            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
