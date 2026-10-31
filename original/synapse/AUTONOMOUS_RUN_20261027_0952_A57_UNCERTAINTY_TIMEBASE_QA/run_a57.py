"""A57 CLI: read-only telemetry evaluation, JSON to stdout or a new file.
Usage: python run_a57.py telemetry.csv metadata.json uncertainty.json [--output report.json]
Output never grants physical release. Refuses to overwrite an existing report.
"""
import argparse
import json
from pathlib import Path

from a57_uncertainty_gate import audit


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv", type=Path)
    p.add_argument("metadata", type=Path)
    p.add_argument("uncertainty", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = audit(a.csv, a.metadata, a.uncertainty)
    rendered = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if a.output:
        # Exclusive creation: no silent replacement of existing evidence.
        with a.output.open("x", encoding="utf-8") as f:
            f.write(rendered)
        print("A57_REPORT_WRITTEN", a.output)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
