"""Run every sql/*.sql file against the cleaned CSVs using in-memory DuckDB."""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = PROCESSED / "sql_results"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for table in ["customers", "accounts", "transactions"]:
        con.execute(f"CREATE VIEW {table} AS SELECT * FROM read_csv_auto('{(PROCESSED / f'cleaned_{table}.csv').as_posix()}')")
    for path in sorted((ROOT / "sql").glob("*.sql")):
        body = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--"))
        statements = [x.strip() for x in body.split(";") if x.strip()]
        for i, stmt in enumerate(statements, 1):
            frame = con.execute(stmt).df()
            target = OUT / f"{path.stem}_{i}.csv"
            frame.to_csv(target, index=False)
            print(f"[OK] {path.name} #{i}: {len(frame)} rows -> {target.name}")
    print("SQL queries executed successfully.")


if __name__ == "__main__":
    main()
