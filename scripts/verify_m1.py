"""Run CodePick M1 with separate repository interpreters and disposable storage."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


MARKER = "CodePick M1 disposable integration fixture v1\n"
STAGES = (
    ("ingest", "deepdata"),
    ("enrich", "seek_data"),
    ("replay", "seek_data"),
    ("score", "agentic"),
    ("read", "agentic"),
    ("update", "deepdata"),
    ("versions", "seek_data"),
)


def run(project_root: Path, data_dir: Path) -> dict:
    script = Path(__file__).with_name("m1_stage.py")
    results = []
    environment = os.environ.copy()
    # Each stage selects its new test databases explicitly. Strip inherited
    # runtime switches so a developer's shell cannot redirect the gate.
    for key in (
        "DATABASE_URL", "L1_DATABASE_URL", "L2_DATABASE_URL", "L2_L1_DATABASE_URL",
        "L3_MIGRATION_SMOKE_DATABASE_URL", "PYTHONPATH",
    ):
        environment.pop(key, None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for stage, repo in STAGES:
        executable = project_root / repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not executable.is_file():
            raise RuntimeError(f"Missing {repo} virtual environment: {executable}")
        command = [str(executable), str(script), stage, "--data-dir", str(data_dir), "--project-root", str(project_root)]
        completed = subprocess.run(
            command, cwd=project_root / repo, env=environment,
            text=True, encoding="utf-8", capture_output=True, timeout=180,
        )
        if completed.returncode:
            detail = (completed.stdout + "\n" + completed.stderr)[-12000:]
            raise RuntimeError(f"M1 stage {stage} failed ({completed.returncode}):\n{detail}")
        result = json.loads((data_dir / f"{stage}.json").read_text(encoding="utf-8"))
        results.append(result)
        print(f"M1 {stage}: PASS ({repo}, separate process)", flush=True)
    return {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "stages": results,
        "boundary": {
            "databases": "Three independent temporary SQLite databases",
            "source": "Local RSS/HTML processed by the actual L0 ingestion code",
            "models": "L1 and L2 FakeLLM; no external model calls",
            "delivery": "L0 envelope fixture and L1 outbox to a local durable envelope file; no Redis worker",
            "version_processing": "L0 update is explicitly re-read; upstream update notifications and L2 version rescoring are not verified",
            "not_verified": ["PostgreSQL", "Redis", "S3", "L2 HTTP/L3 reader", "production readiness"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--data-dir", type=Path, help="Keep results in a NEW directory; existing paths are refused")
    parser.add_argument("--report", type=Path, help="Write a reusable JSON verification record")
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    if args.data_dir:
        data_dir = args.data_dir.resolve()
        data_dir.mkdir(parents=True, exist_ok=False)
        (data_dir / ".codepick-m1-fixture").write_text(MARKER, encoding="utf-8")
        report = run(project_root, data_dir)
        report["retained_data_dir"] = str(data_dir)
    else:
        with TemporaryDirectory(prefix="codepick-m1-") as temporary:
            data_dir = Path(temporary)
            (data_dir / ".codepick-m1-fixture").write_text(MARKER, encoding="utf-8")
            report = run(project_root, data_dir)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CODEPICK M1: PASS (L0 -> durable L1 -> L2; restart and version checks)")


if __name__ == "__main__":
    main()
