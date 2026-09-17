"""Safety and lifecycle regression checks for the local preview launcher."""

from __future__ import annotations

import io
import json
import signal
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

import run_preview


class Response(io.BytesIO):
    status = 200


class PreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="codepick-launcher-test-")
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        for relative in ("l0/l0.db", "l1/l1.db", "l2.db"):
            database = self.data / relative
            database.parent.mkdir(exist_ok=True)
            database.touch()

    def arguments(self, *extra: str):
        return patch(
            "sys.argv", ["run_preview.py", "--data-dir", str(self.data), *extra]
        )

    def test_missing_database_does_not_start_or_migrate(self) -> None:
        (self.data / "l2.db").unlink()
        with (
            self.arguments(),
            patch.object(run_preview.subprocess, "run") as migrate,
            self.assertRaisesRegex(SystemExit, "Missing prepared preview database"),
        ):
            run_preview.main()
        migrate.assert_not_called()

    def test_duplicate_and_privileged_ports_are_rejected(self) -> None:
        for options in (("--web-port", "18100"), ("--web-port", "80")):
            with (
                self.subTest(options=options),
                self.arguments(*options),
                patch.object(run_preview.subprocess, "run") as migrate,
            ):
                with self.assertRaisesRegex(SystemExit, "distinct unprivileged ports"):
                    run_preview.main()
                migrate.assert_not_called()

    def test_occupied_port_does_not_migrate(self) -> None:
        with self.arguments(), patch.object(run_preview.socket, "socket") as socket:
            socket.return_value.__enter__.return_value.bind.side_effect = OSError(
                "busy"
            )
            with patch.object(run_preview.subprocess, "run") as migrate:
                with self.assertRaisesRegex(SystemExit, "already in use"):
                    run_preview.main()
                migrate.assert_not_called()

    def run_fake_services(self, *, items: list[dict], early_exit: bool = False):
        processes = [Mock(pid=91000 + index) for index in range(4)]
        for process in processes:
            process.poll.return_value = 1 if early_exit else None
        with ExitStack() as stack:
            stack.enter_context(self.arguments())
            socket = stack.enter_context(patch.object(run_preview.socket, "socket"))
            migrate = stack.enter_context(patch.object(run_preview.subprocess, "run"))
            spawn = stack.enter_context(
                patch.object(run_preview.subprocess, "Popen", side_effect=processes)
            )
            stack.enter_context(patch.object(run_preview.signal, "signal"))
            kill = stack.enter_context(patch.object(run_preview.os, "killpg"))
            stack.enter_context(
                patch.object(run_preview.time, "sleep", side_effect=KeyboardInterrupt)
            )
            stack.enter_context(
                patch.object(
                    run_preview,
                    "urlopen",
                    side_effect=lambda *a, **kw: Response(
                        json.dumps({"items": items, "total": len(items)}).encode()
                    ),
                )
            )
            output = stack.enter_context(patch("sys.stdout", new_callable=io.StringIO))
            stack.enter_context(
                patch.dict(
                    run_preview.os.environ,
                    {
                        "DATABASE_URL": "postgresql://must-not-use/business",
                        "L3_USE_STUB_L2": "true",
                        "READER_USE_DEMO_FALLBACK": "true",
                        "L2_API_KEY": "must-not-inherit",
                        "L2_L1_CONTENTS_TABLE": "private",
                    },
                )
            )
            error = None
            try:
                run_preview.main()
            except RuntimeError as exc:
                error = str(exc)
            return socket, migrate, spawn, kill, output.getvalue(), error

    def test_ready_is_loopback_only_explicit_sqlite_and_children_are_cleaned(
        self,
    ) -> None:
        socket, migrate, spawn, kill, output, error = self.run_fake_services(
            items=[{"id": "1"}]
        )
        self.assertIsNone(error)
        self.assertIn('"status": "ready"', output)
        binds = socket.return_value.__enter__.return_value.bind.call_args_list
        self.assertEqual(
            [call.args[0] for call in binds],
            [("127.0.0.1", port) for port in (13200, 18100, 18230, 18000)],
        )
        self.assertEqual(
            migrate.call_args.kwargs["env"]["DATABASE_URL"],
            f"sqlite:///{self.data / 'l3.db'}",
        )
        self.assertEqual(
            migrate.call_args.args[0][-5:],
            ["alembic", "-c", "db/alembic.ini", "upgrade", "head"],
        )
        self.assertEqual(spawn.call_count, 4)
        for call in spawn.call_args_list:
            env = call.kwargs["env"]
            self.assertEqual(env["L2_PROCESSING_MODE"], "heuristic")
            self.assertEqual(env["L3_USE_STUB_L2"], "false")
            self.assertEqual(env["READER_USE_DEMO_FALLBACK"], "false")
            self.assertEqual(env["EMAIL_PROVIDER"], "mock")
            self.assertEqual(env["BILLING_ENVIRONMENT"], "sandbox")
            self.assertNotIn("L2_API_KEY", env)
            self.assertNotIn("L2_L1_CONTENTS_TABLE", env)
            self.assertTrue(call.kwargs["start_new_session"])
        l0 = spawn.call_args_list[0]
        self.assertIn("--read-only", l0.args[0])
        self.assertEqual(
            l0.kwargs["env"]["DATABASE_URL"], f"sqlite:///{self.data / 'l0/l0.db'}"
        )
        self.assertEqual(kill.call_count, 4)
        self.assertEqual(kill.call_args_list[0].args, (91003, signal.SIGTERM))

    def test_empty_feed_is_not_reported_as_ready_and_all_children_stop(self) -> None:
        _, _, _, kill, output, error = self.run_fake_services(items=[])
        self.assertEqual(error, "Preview has no readable completed content")
        self.assertNotIn('"status": "ready"', output)
        self.assertEqual(kill.call_count, 4)

    def test_failed_child_is_reported_and_started_children_stop(self) -> None:
        _, _, spawn, kill, output, error = self.run_fake_services(
            items=[], early_exit=True
        )
        self.assertIn("l0 exited", error or "")
        self.assertNotIn('"status": "ready"', output)
        self.assertEqual(spawn.call_count, 1)
        self.assertEqual(kill.call_count, 1)


if __name__ == "__main__":
    unittest.main()
