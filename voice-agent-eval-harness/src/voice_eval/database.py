"""SQLite storage for local annotation state. Judge outputs are never stored here."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from voice_eval.schemas import utc_now

SCHEMA = """
CREATE TABLE IF NOT EXISTS annotations (
    annotation_id  TEXT PRIMARY KEY,
    transcript_id  TEXT NOT NULL,
    annotator_id   TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    status         TEXT NOT NULL,
    payload        TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ann_transcript ON annotations(transcript_id);
CREATE TABLE IF NOT EXISTS annotation_batches (
    batch_id       TEXT PRIMARY KEY,
    annotator_id   TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    frozen_at      TEXT NOT NULL,
    n_annotations  INTEGER NOT NULL,
    export_path    TEXT NOT NULL,
    export_sha256  TEXT NOT NULL,
    sample_ids     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    action        TEXT NOT NULL,
    annotation_id TEXT,
    details       TEXT
);
"""


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def audit(
    conn: sqlite3.Connection,
    action: str,
    annotation_id: str | None = None,
    details: dict | None = None,
) -> None:
    conn.execute(
        "INSERT INTO audit_log (ts, action, annotation_id, details) VALUES (?, ?, ?, ?)",
        (utc_now(), action, annotation_id, json.dumps(details or {})),
    )
