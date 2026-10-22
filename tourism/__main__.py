"""Run the whole pipeline: clean -> SQLite -> SQL analysis -> charts and findings."""
from pathlib import Path

from .database import ROOT, build_database
from .report import write_report


def main() -> None:
    db_path = build_database(ROOT / "build" / "tourism.sqlite")
    print(f"Database built: {db_path.relative_to(ROOT)}")
    for path in write_report(db_path, ROOT / "outputs"):
        print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
