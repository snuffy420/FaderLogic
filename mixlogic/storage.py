"""Local saved imports and session state, kept beside the portable application."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def track_snapshot(tracks):
    """Keep track metadata and order; waveforms already live in their own cache."""
    return [{key: value for key, value in track.items() if key != "waveform"}
            for track in tracks]


class LibraryStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.directory / "library.sqlite3")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS playlists (
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                source_m3u8 TEXT NOT NULL, source_txt TEXT NOT NULL,
                tracks TEXT NOT NULL, imported_at TEXT NOT NULL,
                UNIQUE(source_m3u8, source_txt)
            );
            CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        # Upgrade saved libraries from the first playlist-browser test build.
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(playlists)")}
        if "linked_folder" not in columns:
            with self.conn:
                self.conn.execute("ALTER TABLE playlists ADD COLUMN linked_folder TEXT")

    def list_playlists(self):
        rows = self.conn.execute("SELECT * FROM playlists ORDER BY name COLLATE NOCASE, imported_at").fetchall()
        return [dict(row, track_count=len(json.loads(row["tracks"]))) for row in rows]

    def get_playlist(self, playlist_id):
        row = self.conn.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        if row is None:
            return None
        entry = dict(row)
        entry["tracks"] = json.loads(entry["tracks"])
        return entry

    def find_import(self, m3u8, txt):
        row = self.conn.execute(
            "SELECT id FROM playlists WHERE source_m3u8 = ? AND source_txt = ?",
            (os.path.normcase(os.path.abspath(m3u8)), os.path.normcase(os.path.abspath(txt)) if txt else "")
        ).fetchone()
        return self.get_playlist(row["id"]) if row else None

    def add_playlist(self, m3u8, txt, tracks):
        # Parse the original before copying it: relative audio paths refer to its directory.
        display_name = Path(m3u8).stem
        m3u8 = os.path.normcase(os.path.abspath(m3u8))
        txt = os.path.normcase(os.path.abspath(txt)) if txt else ""
        sources = [("playlist.m3u8", Path(m3u8).read_bytes())]
        if txt:
            sources.append(("metadata.txt", Path(txt).read_bytes()))
        previous = self.conn.execute(
            "SELECT id, name FROM playlists WHERE source_m3u8 = ? AND source_txt = ?", (m3u8, txt)
        ).fetchone()
        playlist_id = previous["id"] if previous else uuid4().hex
        name = previous["name"] if previous else display_name
        folder = self.directory / "sources" / playlist_id
        folder.mkdir(parents=True, exist_ok=True)
        for filename, content in sources:
            temporary = folder / (filename + ".tmp")
            temporary.write_bytes(content)
            os.replace(temporary, folder / filename)
        with self.conn:
            self.conn.execute("""
                INSERT INTO playlists (id, name, source_m3u8, source_txt, tracks, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET tracks = excluded.tracks,
                    imported_at = excluded.imported_at
            """, (playlist_id, name, m3u8, txt,
                  json.dumps(track_snapshot(tracks), ensure_ascii=False),
                  datetime.now(timezone.utc).isoformat()))
        return playlist_id

    def update_tracks(self, playlist_id, tracks, linked_folder):
        with self.conn:
            self.conn.execute("UPDATE playlists SET tracks = ?, linked_folder = ? WHERE id = ?",
                              (json.dumps(track_snapshot(tracks), ensure_ascii=False), linked_folder, playlist_id))

    def rename(self, playlist_id, name):
        name = name.strip()
        if not name:
            raise ValueError("Enter a playlist name.")
        with self.conn:
            self.conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (name, playlist_id))

    def remove(self, playlist_id):
        with self.conn:
            self.conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        # Keep the saved source exports, so removing a browser entry never deletes files.

    def load_session(self):
        row = self.conn.execute("SELECT value FROM state WHERE key = 'session'").fetchone()
        return json.loads(row[0]) if row else {}

    def save_session(self, session):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO state VALUES ('session', ?)",
                              (json.dumps(session, ensure_ascii=False),))

    def close(self):
        self.conn.close()
