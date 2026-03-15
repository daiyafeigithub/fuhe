#!/usr/bin/env python3
"""Import/update tcm_medicine_dict records from CSV.

Expected CSV columns:
- 序号, 商品名, 规格, 单位, CJID

Rules:
- Remove bracketed English tags in medicine_name, e.g. (JZ), （JZ）, （JZ), (JZ）
- Keep Chinese bracket notes intact, e.g. 附片（黑顺片）
- Upsert by CJID
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


# Remove only bracket groups containing English letters (and optional spaces).
EN_BRACKET_PATTERN = re.compile(r"[（(]\s*[A-Za-z]+\s*[)）]")

HEADER_ALIASES = {
    "name": ("商品名", "品名", "medicine_name", "name"),
    "spec": ("规格", "specification", "spec"),
    "unit": ("单位", "unit"),
    "cjid": ("CJID", "cjid", "cj_id", "院内编码", "编码"),
}


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


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", "", (value or "")).strip().lower()


def resolve_columns(fieldnames: list[str]) -> dict[str, str]:
    normalized_to_original = {
        normalize_header(name): name
        for name in fieldnames
        if name is not None
    }

    resolved: dict[str, str] = {}
    for key, aliases in HEADER_ALIASES.items():
        found = None
        for alias in aliases:
            candidate = normalized_to_original.get(normalize_header(alias))
            if candidate:
                found = candidate
                break
        if not found:
            raise RuntimeError(
                f"Missing CSV column for '{key}'. Existing columns: {fieldnames}"
            )
        resolved[key] = found

    return resolved


def parse_cjid(value: str, line_no: int) -> int:
    raw = (value or "").strip()
    if not raw:
        raise RuntimeError(f"Missing CJID at CSV line {line_no}")

    if re.fullmatch(r"\d+", raw):
        return int(raw)
    if re.fullmatch(r"\d+\.0+", raw):
        return int(raw.split(".", 1)[0])

    raise RuntimeError(f"Invalid CJID '{raw}' at CSV line {line_no}")


def parse_csv(input_path: Path, encoding: str) -> list[Item]:
    with input_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError("CSV header not found")

        columns = resolve_columns(reader.fieldnames)
        items: list[Item] = []

        for line_no, row in enumerate(reader, start=2):
            name_raw = (row.get(columns["name"]) or "").strip()
            spec_raw = (row.get(columns["spec"]) or "").strip()
            unit_raw = (row.get(columns["unit"]) or "").strip()
            cjid_raw = (row.get(columns["cjid"]) or "").strip()

            if not any([name_raw, spec_raw, unit_raw, cjid_raw]):
                continue

            cjid = parse_cjid(cjid_raw, line_no)
            if not name_raw:
                raise RuntimeError(f"Missing medicine_name at CSV line {line_no}")

            items.append(
                Item(
                    medicine_name=normalize_name(name_raw),
                    specification=spec_raw,
                    unit=unit_raw or "包",
                    cjid=cjid,
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
    parser = argparse.ArgumentParser(description="Import tcm_medicine_dict into sqlite (CSV only)")
    parser.add_argument("--db", required=True, help="SQLite DB path")
    parser.add_argument("--input", required=True, help="CSV file path")
    parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig)")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser().resolve()
    input_path = Path(args.input).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".csv":
        raise RuntimeError(f"Only CSV is supported. Got: {input_path.name}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    items = parse_csv(input_path, args.encoding)
    if not items:
        raise RuntimeError("No valid rows parsed from CSV file")

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
