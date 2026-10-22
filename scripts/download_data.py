"""Re-download the two source files from Open Data Torino into data/raw/.

The repository already contains copies, so this is only needed to refresh them.
Data: Comune di Torino / ARPA Piemonte, licence CC BY 4.0.
"""
import urllib.request
from pathlib import Path

BASE = "https://risorse.comune.torino.it/opendata/turismo/"
FILES = [
    "esercizi_turistici_provTO_1994-2018.csv",
    "arrivi_turisti_provTO_1994-2018.csv",
]
TARGET = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        with urllib.request.urlopen(BASE + name, timeout=30) as response:
            content = response.read()
        if not content.strip():
            raise SystemExit(f"{name}: downloaded file is empty")
        (TARGET / name).write_bytes(content)
        print(f"Saved {name} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
