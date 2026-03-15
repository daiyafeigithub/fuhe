#!/usr/bin/env python3
"""Import/update tcm_medicine_dict records from a TSV-like text file.

Expected columns (tab-separated preferred):
序号\t商品名\t规格\t单位\tCJID

Rules:
- Remove bracketed English letters in medicine name, e.g. (JZ), （JZ）, （JZ), (JZ）
- Keep other bracketed Chinese text intact, e.g. 附片（黑顺片）
- Upsert by CJID
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


HEADER_KEYWORDS = ("序号", "商品名", "规格", "单位", "CJID")
# Remove only bracket groups containing English letters (and optional spaces), not Chinese text.
EN_BRACKET_PATTERN = re.compile(r"[（(]\s*[A-Za-z]+\s*[)）]")
SPLIT_PATTERN = re.compile(r"^\s*(\d+)\s+(.+?)\s+([^\s]+)\s+([^\s]+)\s+(\d+)\s*$")


@dataclass
class Item:
    medicine_name: str
    specification: str
    unit: str
    cjid: int


def normalize_name(name: str) -> str:
    cleaned = EN_BRACKET_PATTERN.sub("", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_lines(lines: Iterable[str]) -> list[Item]:
    items: list[Item] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if all(k in line for k in HEADER_KEYWORDS):
            continue

        parts = line.split("\t")
        if len(parts) >= 5 and parts[0].strip().isdigit():
            _, name, spec, unit, cjid = parts[:5]
        else:
            m = SPLIT_PATTERN.match(line)
            if not m:
                continue
            _, name, spec, unit, cjid = m.groups()

        items.append(
            Item(
                medicine_name=normalize_name(name),
                specification=spec.strip(),
                unit=unit.strip() or "包",
                cjid=int(str(cjid).strip()),
            )
        )

    # Deduplicate by CJID, keeping the last occurrence.
    dedup: dict[int, Item] = {}
    for it in items:
        dedup[it.cjid] = it
    return list(dedup.values())


def ensure_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tcm_medicine_dict (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            cjid INTEGER NOT NULL UNIQUE,
            product_code TEXT,
            specification TEXT,
            unit TEXT DEFAULT '包',
            status INTEGER DEFAULT 1,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def upsert_items(conn: sqlite3.Connection, items: list[Item]) -> tuple[int, int]:
    cur = conn.cursor()
    ensure_table(cur)

    inserted = 0
    updated = 0

    for it in items:
        exists = cur.execute(
            "SELECT 1 FROM tcm_medicine_dict WHERE cjid = ?",
            (it.cjid,),
        ).fetchone()

        cur.execute(
            """
            INSERT INTO tcm_medicine_dict
                (medicine_name, cjid, product_code, specification, unit, status)
            VALUES
                (?, ?, NULL, ?, ?, 1)
            ON CONFLICT(cjid) DO UPDATE SET
                medicine_name = excluded.medicine_name,
                specification = excluded.specification,
                unit = excluded.unit,
                status = 1,
                update_time = CURRENT_TIMESTAMP
            """,
            (it.medicine_name, it.cjid, it.specification, it.unit),
        )

        if exists:
            updated += 1
        else:
            inserted += 1

    conn.commit()
    return inserted, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Import tcm_medicine_dict into sqlite")
    parser.add_argument("--db", required=True, help="SQLite DB path")
    parser.add_argument("--input", required=False, help="Input text/tsv path. If omitted, read from stdin")
    parser.add_argument("--encoding", default="utf-8", help="Input file encoding (default: utf-8)")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    if args.input:
        input_path = Path(args.input).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        text = input_path.read_text(encoding=args.encoding)
    else:
        text = sys.stdin.read()
        if not text.strip():
            raise RuntimeError("No input received from stdin")

    items = parse_lines(text.splitlines())

    if not items:
        raise RuntimeError("No valid rows parsed from input file")

    with sqlite3.connect(str(db_path)) as conn:
        inserted, updated = upsert_items(conn, items)
        total = conn.execute("SELECT COUNT(*) FROM tcm_medicine_dict").fetchone()[0]

    print(f"Parsed rows: {len(items)}")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Total in table: {total}")
    print(f"DB: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
