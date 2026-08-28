#!/usr/bin/env python3
"""
Start the AutoSCM React frontend (Vite dev server) as a detached background daemon.
Usage:
    python scripts/start_frontend.py [--port 5173]
"""
import argparse
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend-react"
NPM = "npm"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5173)
    args = parser.parse_args()
    port = str(args.port)

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
    }
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", port, "--strictPort"],
        cwd=str(FRONTEND),
        stdout=open("/tmp/frontend_dev.log", "w"),
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    time.sleep(4)
    print(f"Frontend launched as PID {proc.pid} on port {port}")
    print("Log: /tmp/frontend_dev.log")


if __name__ == "__main__":
    main()
