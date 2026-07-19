from pathlib import Path

from sentinel.db import get_pool


def main():
    schema = (Path(__file__).resolve().parent / "schema.sql").read_text()
    pool = get_pool()
    with pool.connection() as conn:
        for stmt in schema.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(s + ";")
        conn.commit()
    print("Schema applied.")


if __name__ == "__main__":
    main()
