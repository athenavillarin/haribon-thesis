"""HARIBON — Thesis Task 5: Consolidated Tables + Figures

Usage:
    cd task_5
    python run_task5.py

This runs the Task 5 generator in `task_5/code/` and writes outputs to:
    - task_5/results/
    - task_5/figures/
"""

from __future__ import annotations

import os
import subprocess
import sys


def _run(command: str, description: str) -> None:
    print("\n" + "=" * 72)
    print(description)
    print("=" * 72)
    result = subprocess.run(
        command,
        shell=True,
        text=True,
        cwd=os.path.dirname(__file__),
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    base_dir = os.path.dirname(__file__)
    generator = os.path.join(base_dir, "code", "task5_generate_deliverables.py")
    if not os.path.exists(generator):
        print(f"Error: expected {generator}")
        sys.exit(1)

    _run("python code\\task5_generate_deliverables.py", "Generate Task 5 deliverables")


if __name__ == "__main__":
    main()
