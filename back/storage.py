from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).with_name("defense_first.db")))


SEED_DEPARTMENTS = [
    ("DAPA-OPS", "방산보안대응팀"),
    ("RND-LAB", "무기체계연구소"),
    ("SUPPLY-7", "협력업체보안실"),
]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def operator_in_department(department_id: int, operator_id: int) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM operators WHERE id = ? AND department_id = ?",
            (operator_id, department_id),
        ).fetchone()
    return row is not None


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(department_id, name),
                FOREIGN KEY(department_id) REFERENCES departments(id)
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                input_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(department_id) REFERENCES departments(id),
                FOREIGN KEY(created_by) REFERENCES operators(id)
            );

            CREATE TABLE IF NOT EXISTS case_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                operator_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES cases(id),
                FOREIGN KEY(operator_id) REFERENCES operators(id)
            );
            """
        )
        for code, name in SEED_DEPARTMENTS:
            conn.execute(
                "INSERT OR IGNORE INTO departments(code, name) VALUES(?, ?)",
                (code, name),
            )


def get_department_by_code(code: str) -> dict[str, Any] | None:
    normalized = code.strip().upper()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, code, name FROM departments WHERE code = ?",
            (normalized,),
        ).fetchone()
    return dict(row) if row else None


def get_department(department_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, code, name FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()
    return dict(row) if row else None


def get_or_create_operator(department_id: int, name: str) -> dict[str, Any]:
    clean_name = name.strip()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO operators(department_id, name)
            VALUES(?, ?)
            """,
            (department_id, clean_name),
        )
        row = conn.execute(
            """
            SELECT id, department_id, name
            FROM operators
            WHERE department_id = ? AND name = ?
            """,
            (department_id, clean_name),
        ).fetchone()
    return dict(row)


def create_case(
    department_id: int,
    operator_id: int,
    mode: str,
    answers: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO cases(
                department_id, created_by, mode, status, input_json, result_json
            )
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                department_id,
                operator_id,
                mode,
                "분석완료",
                json.dumps(answers, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
            ),
        )
        case_id = cursor.lastrowid
    return get_case(case_id)


def list_cases(department_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                c.id, c.department_id, c.created_by, c.mode, c.status,
                c.input_json, c.result_json, c.created_at, c.updated_at,
                o.name AS created_by_name
            FROM cases c
            JOIN operators o ON o.id = c.created_by
            WHERE c.department_id = ?
            ORDER BY c.updated_at DESC, c.id DESC
            """,
            (department_id,),
        ).fetchall()
    return [_decode_case(dict(row)) for row in rows]


def get_case(case_id: int) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                c.id, c.department_id, c.created_by, c.mode, c.status,
                c.input_json, c.result_json, c.created_at, c.updated_at,
                o.name AS created_by_name
            FROM cases c
            JOIN operators o ON o.id = c.created_by
            WHERE c.id = ?
            """,
            (case_id,),
        ).fetchone()
    if row is None:
        raise KeyError(case_id)
    return _decode_case(dict(row))


def update_case_status(case_id: int, department_id: int, status: str) -> dict[str, Any]:
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE cases
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND department_id = ?
            """,
            (status, case_id, department_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(case_id)
    return get_case(case_id)


def add_case_note(case_id: int, department_id: int, operator_id: int, note: str) -> dict[str, Any]:
    with connect() as conn:
        exists = conn.execute(
            "SELECT id FROM cases WHERE id = ? AND department_id = ?",
            (case_id, department_id),
        ).fetchone()
        if exists is None:
            raise KeyError(case_id)
        cursor = conn.execute(
            """
            INSERT INTO case_notes(case_id, operator_id, note)
            VALUES(?, ?, ?)
            """,
            (case_id, operator_id, note.strip()),
        )
        conn.execute(
            "UPDATE cases SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (case_id,),
        )
        note_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT n.id, n.case_id, n.operator_id, n.note, n.created_at, o.name AS operator_name
            FROM case_notes n
            JOIN operators o ON o.id = n.operator_id
            WHERE n.id = ?
            """,
            (note_id,),
        ).fetchone()
    return dict(row)


def list_case_notes(case_id: int, department_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        exists = conn.execute(
            "SELECT id FROM cases WHERE id = ? AND department_id = ?",
            (case_id, department_id),
        ).fetchone()
        if exists is None:
            raise KeyError(case_id)
        rows = conn.execute(
            """
            SELECT n.id, n.case_id, n.operator_id, n.note, n.created_at, o.name AS operator_name
            FROM case_notes n
            JOIN operators o ON o.id = n.operator_id
            WHERE n.case_id = ?
            ORDER BY n.created_at DESC, n.id DESC
            """,
            (case_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _decode_case(row: dict[str, Any]) -> dict[str, Any]:
    row["input"] = json.loads(row.pop("input_json"))
    row["result"] = json.loads(row.pop("result_json"))
    return row
