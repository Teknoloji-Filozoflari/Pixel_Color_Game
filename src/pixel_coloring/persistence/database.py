import json
import math
import sqlite3
import time
from contextlib import contextmanager

import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS paintings (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, author TEXT, category TEXT,
 width INTEGER, height INTEGER, palette_size INTEGER, data_path TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS progress (
 painting_id TEXT PRIMARY KEY REFERENCES paintings(id), completion_percentage REAL,
 painted_count INTEGER, elapsed_seconds REAL, last_played REAL,
 save_version INTEGER, progress_blob BLOB, selected_color INTEGER
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS view_states (
 painting_id TEXT PRIMARY KEY REFERENCES paintings(id) ON DELETE CASCADE,
 zoom REAL NOT NULL, center_x REAL NOT NULL, center_y REAL NOT NULL,
 width INTEGER NOT NULL, height INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS statistics (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS achievements (id TEXT PRIMARY KEY, unlocked INTEGER, unlocked_at REAL);
PRAGMA user_version=1;
"""


class Database:
    def __init__(self, path):
        self.path = path
        with self.connect() as con:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise ValueError("Veritabanı daha yeni bir oyun sürümüyle oluşturulmuş")
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(SCHEMA)
            con.execute("DELETE FROM statistics")
            con.execute("DELETE FROM achievements")
            con.execute("UPDATE progress SET elapsed_seconds=0, last_played=0")

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with con:
                yield con
        finally:
            con.close()

    def register(self, painting, path):
        self.register_many([(painting, path)])

    def register_many(self, entries):
        """Register a collection in one transaction without touching saved masks."""
        with self.connect() as con:
            con.executemany(
                """INSERT INTO paintings VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET data_path=excluded.data_path""",
                [(
                    painting.id,
                    painting.title,
                    painting.author,
                    painting.category,
                    painting.width,
                    painting.height,
                    len(painting.palette),
                    str(path),
                    time.time(),
                ) for painting, path in entries],
            )

    def save(self, snapshot, view_state=None):
        snapshot = (*snapshot[:3], 0, 0, *snapshot[5:])
        with self.connect() as con:
            con.execute("INSERT OR REPLACE INTO progress VALUES (?,?,?,?,?,?,?,?)", snapshot)
            if view_state is not None:
                con.execute(
                    "INSERT OR REPLACE INTO view_states VALUES (?,?,?,?,?,?)",
                    (snapshot[0], view_state['zoom'], view_state['center_x'], view_state['center_y'],
                     view_state['width'], view_state['height']),
                )

    def load_view(self, painting):
        with self.connect() as con:
            row = con.execute(
                "SELECT zoom,center_x,center_y,width,height FROM view_states WHERE painting_id=?",
                (painting.id,),
            ).fetchone()
        if row is None or row[3:] != (painting.width, painting.height):
            return None
        zoom, x, y, width, height = row
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (zoom, x, y)):
            return None
        if not .05 <= zoom <= 10000:
            return None
        return dict(zoom=zoom, center_x=x, center_y=y, width=width, height=height)

    def load(self, painting):
        with self.connect() as con:
            row = con.execute(
                "SELECT save_version,progress_blob,elapsed_seconds,selected_color "
                "FROM progress WHERE painting_id=?",
                (painting.id,),
            ).fetchone()
        if row is None:
            return 0.0, None
        version, blob, elapsed, selected = row
        expected = (painting.target_map.size + 7) // 8
        if version != 1 or len(blob) != expected:
            raise ValueError("Kayıt bozuk veya kayıt sürümü desteklenmiyor")
        bits = np.unpackbits(np.frombuffer(blob, dtype=np.uint8), count=painting.target_map.size)
        painting.restore(bits.reshape(painting.target_map.shape).astype(bool))
        return max(0, elapsed), max(0, min(len(painting.palette) - 1, selected))

    def progress_map(self):
        with self.connect() as con:
            rows = con.execute(
                "SELECT painting_id,completion_percentage,painted_count,elapsed_seconds,"
                "last_played FROM progress ORDER BY last_played DESC"
            ).fetchall()
        return {r[0]: r[1:] for r in rows}

    def get_settings(self):
        with self.connect() as con:
            return {k: json.loads(v) for k, v in con.execute("SELECT key,value FROM settings")}

    def set_settings(self, settings):
        with self.connect() as con:
            con.executemany(
                "INSERT OR REPLACE INTO settings VALUES (?,?)",
                [(k, json.dumps(v)) for k, v in settings.items()],
            )
