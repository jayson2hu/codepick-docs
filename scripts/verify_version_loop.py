"""Verify L0 update -> Redis -> L1 -> Redis -> Arq -> versioned L2."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def run_command(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    label: str,
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=180,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode:
        raise RuntimeError(f"{label} failed ({completed.returncode}):\n{output[-12000:]}")
    print(f"{label}: PASS", flush=True)
    return output


def run(project_root: Path, data_dir: Path, redis_url: str) -> dict[str, object]:
    stage_script = Path(__file__).with_name("version_loop_stage.py")
    l0_queue = "codepick:version-loop:l0"
    l1_queue = "codepick:version-loop:l1"
    environment = os.environ.copy()
    environment.update({
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "L0_DATABASE_URL": f"sqlite:///{data_dir / 'l0.db'}",
        "L0_OBJECT_STORE_PATH": str(data_dir / "objects"),
        "L1_DATABASE_URL": f"sqlite:///{data_dir / 'l1.db'}",
        "L1_REDIS_URL": redis_url,
        "L2_REDIS_URL": redis_url,
        "L2_DATABASE_URL": f"sqlite:///{data_dir / 'l2.db'}",
        "L2_L1_DATABASE_URL": f"sqlite:///{data_dir / 'l1.db'}",
        "L2_ANALYSIS_PROVIDER": "sqlalchemy",
        "L0_EVENT_QUEUE": l0_queue,
        "L1_EVENT_QUEUE": l1_queue,
        "L2_EVENT_QUEUE": l1_queue,
    })
    executables = {
        repo: project_root / repo / ".venv" / "bin" / "python"
        for repo in ("deepdata", "seek_data", "agentic")
    }
    for repo, executable in executables.items():
        if not executable.is_file():
            raise RuntimeError(f"missing {repo} environment: {executable}")

    def stage(name: str, repo: str, *extra: str) -> str:
        return run_command(
            [
                str(executables[repo]),
                str(stage_script),
                name,
                "--data-dir",
                str(data_dir),
                "--redis-url",
                redis_url,
                "--l0-queue",
                l0_queue,
                "--l1-queue",
                l1_queue,
                *extra,
            ],
            cwd=project_root / repo,
            environment=environment,
            label=f"version-loop {name}",
        )

    def module(repo: str, name: str, *args: str) -> str:
        return run_command(
            [str(executables[repo]), "-m", name, *args],
            cwd=project_root / repo,
            environment=environment,
            label=name,
        )

    def arq_worker() -> str:
        executable = project_root / "agentic" / ".venv" / "bin" / "arq"
        return run_command(
            [
                str(executable),
                "judgment_graph.workers.scoring.worker.WorkerSettings",
                "--burst",
            ],
            cwd=project_root / "agentic",
            environment=environment,
            label="L2 Arq burst worker",
        )

    stage("flush", "agentic")
    stage("seed", "deepdata")
    module("seek_data", "l1_data_processing.worker", "--once")
    module("seek_data", "l1_data_processing.relay", "--once")
    stage("prepare-l2", "agentic")
    module("agentic", "judgment_graph.scripts.consume_events", "--once")
    arq_worker()
    stage("verify", "agentic", "--expected-revision", "1", "--expected-events", "1")

    stage("update", "deepdata")
    module("seek_data", "l1_data_processing.worker", "--once")
    module("seek_data", "l1_data_processing.relay", "--once")
    module("agentic", "judgment_graph.scripts.consume_events", "--once")
    arq_worker()
    stage("verify", "agentic", "--expected-revision", "2", "--expected-events", "2")

    stage("replay-stale", "agentic")
    module("agentic", "judgment_graph.scripts.consume_events", "--once")
    arq_worker()
    stage("verify", "agentic", "--expected-revision", "2", "--expected-events", "2")
    return {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "redis_url": redis_url,
        "data_dir": str(data_dir),
        "checks": [
            "L0 v1 event delivered and scored",
            "L0 update emitted v2 automatically",
            "L1 durable outbox relayed both runs",
            "L2 accepted revision 2 and emitted a second completion",
            "late revision 1 redelivery did not replace revision 2",
        ],
        "models": "L1 and L2 FakeLLM",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--redis-url",
        default="redis://127.0.0.1:6389/15",
    )
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.data_dir:
        data_dir = args.data_dir.resolve()
        data_dir.mkdir(parents=True, exist_ok=False)
        report = run(args.project_root.resolve(), data_dir, args.redis_url)
    else:
        with TemporaryDirectory(prefix="codepick-version-loop-") as temporary:
            report = run(
                args.project_root.resolve(),
                Path(temporary),
                args.redis_url,
            )
    if args.report:
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print("CODEPICK VERSION LOOP: PASS (L0 v2 -> L1 run -> L2 revision; stale v1 ignored)")


if __name__ == "__main__":
    main()
