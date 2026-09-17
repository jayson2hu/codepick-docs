"""Run the private, real-source CodePick preview; Ctrl+C stops its four services."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--web-port", type=int, default=13200)
    parser.add_argument("--reader-port", type=int, default=18100)
    parser.add_argument("--l2-port", type=int, default=18230)
    parser.add_argument("--l0-port", type=int, default=18000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data = args.data_dir.resolve()
    l1_database = data / "l1" / "l1.db"
    if not l1_database.is_file():
        l1_database = data / "l1.db"
    for database in (data / "l0" / "l0.db", l1_database, data / "l2.db"):
        if not database.is_file():
            raise SystemExit(f"Missing prepared preview database: {database}")
    ports = (args.web_port, args.reader_port, args.l2_port, args.l0_port)
    if len(set(ports)) != 4 or any(port < 1024 or port > 65535 for port in ports):
        raise SystemExit("Choose four distinct unprivileged ports")
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise SystemExit(
                    f"Port {port} is already in use; stop the existing preview first"
                ) from exc

    env = os.environ.copy()
    for key in (
        "PYTHONPATH",
        "L2_API_KEY",
        "L2_L1_CONTENTS_TABLE",
        "L3_MIGRATION_SMOKE_DATABASE_URL",
    ):
        env.pop(key, None)
    env.update(
        {
            "L2_DATABASE_URL": f"sqlite:///{data / 'l2.db'}",
            "L2_L1_DATABASE_URL": f"sqlite:///{l1_database}",
            "L2_PROCESSING_MODE": "heuristic",
            "L2_HTTP_HOST": "127.0.0.1",
            "L2_HTTP_PORT": str(args.l2_port),
            "DATABASE_URL": f"sqlite:///{data / 'l3.db'}",
            "L3_REPOSITORY_BACKEND": "sqlalchemy",
            "L3_QUOTA_BACKEND": "sqlalchemy",
            "L3_USE_STUB_L2": "false",
            "L3_AUTH_LOGIN_MODE": "development",
            "L2_BASE_URL": f"http://127.0.0.1:{args.l2_port}",
            "READER_API_HOST": "127.0.0.1",
            "READER_API_PORT": str(args.reader_port),
            "READER_API_RELOAD": "false",
            "READER_API_BASE": f"http://127.0.0.1:{args.reader_port}",
            "READER_API_PROXY_TARGET": f"http://127.0.0.1:{args.reader_port}",
            "READER_USE_DEMO_FALLBACK": "false",
            "NEXT_TELEMETRY_DISABLED": "1",
            "EMAIL_PROVIDER": "mock",
            "BILLING_ENVIRONMENT": "sandbox",
            "PADDLE_CHECKOUT_BASE_URL": "https://sandbox-payments.codepick.local",
        }
    )
    # Migrations only touch the explicitly selected L3 preview SQLite.
    subprocess.run(
        [
            str(root / "pickblog/.venv/bin/python"),
            "-m",
            "alembic",
            "-c",
            "db/alembic.ini",
            "upgrade",
            "head",
        ],
        cwd=root / "pickblog",
        env=env,
        check=True,
    )
    services = [
        (
            "l0",
            root / "deepdata",
            [
                str(root / "deepdata/.venv/bin/python"),
                "-m",
                "core_data.scripts.dashboard",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.l0_port),
                "--read-only",
            ],
            f"http://127.0.0.1:{args.l0_port}/api/status",
        ),
        (
            "l2",
            root / "agentic",
            [
                str(root / "agentic/.venv/bin/python"),
                "-m",
                "judgment_graph.scripts.run_http",
            ],
            f"http://127.0.0.1:{args.l2_port}/health",
        ),
        (
            "reader",
            root / "pickblog",
            [str(root / "pickblog/.venv/bin/python"), "scripts/run_reader_api.py"],
            f"http://127.0.0.1:{args.reader_port}/api/health",
        ),
        (
            "web",
            root / "pickblog/apps/reader-web",
            [
                "npm",
                "run",
                "dev",
                "--",
                "--hostname",
                "127.0.0.1",
                "--port",
                str(args.web_port),
            ],
            f"http://127.0.0.1:{args.web_port}/zh",
        ),
    ]
    processes: list[tuple[str, subprocess.Popen]] = []
    logs = []
    (data / "logs").mkdir(exist_ok=True)

    def stop(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        for name, cwd, command, health in services:
            log = (data / "logs" / f"{name}.log").open("a", encoding="utf-8")
            logs.append(log)
            service_env = dict(env)
            if name == "l0":
                service_env.update(
                    {
                        "DATABASE_URL": f"sqlite:///{data / 'l0' / 'l0.db'}",
                        "OBJECT_STORE_BACKEND": "file",
                        "OBJECT_STORE_PATH": str(data / "l0" / "objects"),
                    }
                )
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=service_env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            processes.append((name, process))
            deadline = time.monotonic() + 90
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"{name} exited; inspect {data / 'logs'}")
                try:
                    with urlopen(health, timeout=3) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f"{name} did not become ready; inspect {data / 'logs'}"
                    )
                time.sleep(0.5)
        with urlopen(
            f"http://127.0.0.1:{args.web_port}/api/feed?limit=1", timeout=10
        ) as response:
            page = json.load(response)
        if not page.get("items"):
            raise RuntimeError("Preview has no readable completed content")
        print(
            json.dumps(
                {
                    "status": "ready",
                    "web": f"http://127.0.0.1:{args.web_port}/zh",
                    "l0_dashboard": f"http://127.0.0.1:{args.l0_port}",
                    "articles": page["total"],
                    "reader_docs": f"http://127.0.0.1:{args.reader_port}/docs",
                    "l2_docs": f"http://127.0.0.1:{args.l2_port}/docs",
                    "logs": str(data / "logs"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"{name} exited unexpectedly; inspect {data / 'logs'}"
                    )
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping CodePick preview", flush=True)
    finally:
        for _name, process in reversed(processes):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        for log in logs:
            log.close()


if __name__ == "__main__":
    main()
