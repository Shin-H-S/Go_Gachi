"""SQLite DB 상태를 빠르게 확인하는 검증 스크립트.

사용: uv run python scripts/inspect_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("backend/data/app.db")

if not DB_PATH.exists():
    print(f"[!] DB 파일이 없습니다: {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)

tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("테이블:", tables)

for table in tables:
    count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} 행")

# generations가 있으면 상태별 분포도 같이 보여준다.
if "generations" in tables:
    rows = list(conn.execute("SELECT status, count(*) FROM generations GROUP BY status"))
    if rows:
        print("\ngenerations 상태 분포:")
        for status, count in rows:
            print(f"  {status}: {count}")
