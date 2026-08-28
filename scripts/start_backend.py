#!/usr/bin/env python3
"""
Start the AutoSCM backend (FastAPI) as a detached background daemon.
Usage:
    python scripts/start_backend.py [--port 8100]
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_PY = ROOT / ".venv" / "bin" / "python"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()

    proc = subprocess.Popen(
        [str(VENV_PY), "-m", "uvicorn", "main:app", "--port", str(args.port)],
        cwd=str(ROOT),
        stdout=open("/tmp/backend.log", "w"),
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    time.sleep(5)
    print(f"Backend launched as PID {proc.pid} on port {args.port}")
    print("Log: /tmp/backend.log")


if __name__ == "__main__":
    main()
