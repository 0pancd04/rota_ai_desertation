from __future__ import annotations

import sqlite3
from pathlib import Path


def apply_schema(db_path: str, schema_path: str) -> None:
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    sql = Path(schema_path).read_text(encoding="utf-8")
    con = sqlite3.connect(db_path)
    try:
        con.executescript(sql)
        con.commit()
        print("Evaluation schema applied successfully.")
    finally:
        con.close()


if __name__ == "__main__":
    apply_schema("data/rota_operations.db", "evaluation/evaluation_schema.sql")


