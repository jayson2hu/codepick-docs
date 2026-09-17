"""Read-only cross-layer checks against prepared public-source SQLite and local APIs."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def local_base(value: str) -> str:
    parsed = urlparse(value)
    require(
        parsed.scheme == "http" and parsed.hostname == "127.0.0.1",
        "Only explicit loopback HTTP APIs are allowed",
    )
    require(
        not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment,
        "Invalid local API base",
    )
    return value.rstrip("/")


def read_json(url: str) -> dict:
    with urlopen(url, timeout=15) as response:
        return json.load(response)


def verify(data: Path, web: str, l0_api: str, l2_api: str, reader: str) -> dict:
    web, l0_api, l2_api, reader = map(local_base, (web, l0_api, l2_api, reader))
    with ExitStack() as stack:
        databases = []
        for relative in ("l0/l0.db", "l1/l1.db", "l2.db"):
            path = (data / relative).resolve()
            require(path.is_file(), f"Missing preview database: {relative}")
            connection = stack.enter_context(
                closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True))
            )
            connection.row_factory = sqlite3.Row
            databases.append(connection)
        l0, l1, l2 = databases
        sources = {
            str(row["id"]): dict(row)
            for row in l0.execute("SELECT * FROM content_items")
        }
        analyses = {
            row["content_id"]: dict(row)
            for row in l1.execute("SELECT * FROM content_base_analysis")
        }
        states = {
            str(row["content_id"]): dict(row)
            for row in l2.execute("SELECT * FROM content_judgment_state")
        }
        require(
            bool(sources) and sources.keys() == analyses.keys() == states.keys(),
            "All three layers must contain the same imported IDs",
        )
        require(
            l2.execute("SELECT COUNT(*) FROM content_translations").fetchone()[0] == 0,
            "Offline preview must not contain generated translations",
        )
        require(
            all(
                row[0] == "heuristic-v1"
                for row in l2.execute("SELECT model FROM content_vertical_scores")
            ),
            "Unexpected non-heuristic score",
        )
        items = []
        for identity, row in analyses.items():
            source, state = sources[identity], states[identity]
            snapshot, analysis = (
                json.loads(row["input_snapshot"]),
                json.loads(row["analysis"]),
            )
            metadata = snapshot["metadata"]
            require(
                snapshot["source_url"] == source["canonical_url"],
                f"Source URL changed: {identity}",
            )
            require(
                urlparse(snapshot["source_url"]).scheme == "https",
                f"Expected public HTTPS source: {identity}",
            )
            require(
                metadata["content_version"] == source["current_version"]
                and metadata["l0_content_hash"] == source["content_hash"],
                f"L0 version identity mismatch: {identity}",
            )
            require(
                (state["source_run_id"], state["source_revision"])
                == (row["run_id"], row["revision"]),
                f"L2 accepted the wrong snapshot: {identity}",
            )
            require(
                metadata["processing"]["method"].startswith("extractive-")
                and metadata["processing"]["generated"] is False,
                f"Wrong processing provenance: {identity}",
            )
            require(
                0 < len(analysis["summary"]) <= 800,
                f"Unreadable summary length: {identity}",
            )
            points = analysis["key_points"]
            original = f"{snapshot['title']} {snapshot['body']}"
            require(
                0 < len(points) <= 5 and all(point in original for point in points),
                f"Key points must be literal source excerpts: {identity}",
            )
            require(
                not any(
                    noise in analysis["summary"]
                    for noise in (
                        "Try GitHub Copilot app",
                        "Attend GitHub Universe",
                        "Related posts",
                    )
                ),
                f"Navigation leaked into analysis: {identity}",
            )
            items.append(
                {
                    "content_id": identity,
                    "title": snapshot["title"],
                    "source_url": snapshot["source_url"],
                    "l0_version": source["current_version"],
                    "l1_revision": row["revision"],
                    "l1_run_id": row["run_id"],
                    "status": state["status"],
                    "summary_chars": len(analysis["summary"]),
                    "key_points": len(points),
                }
            )

    expected = {
        identity for identity, state in states.items() if state["status"] == "COMPLETED"
    }
    require(bool(expected), "No completed articles available")
    feed = read_json(web + "/api/feed?limit=50")
    require(
        {item["id"] for item in feed["items"]} == expected
        and feed["total"] == len(expected),
        "Web feed differs from persisted completed L2 content",
    )
    for item in feed["items"]:
        identity = item["id"]
        detail = read_json(web + "/api/read/" + identity)
        require(
            detail["url"] == sources[identity]["canonical_url"],
            f"L3 source URL mismatch: {identity}",
        )
        require(
            detail["provenance"]["scoring_method"] == "heuristic"
            and detail["provenance"]["source_kind"] == "public_feed",
            f"L3 lost processing provenance: {identity}",
        )
        require(
            detail["translations"] == {}, f"Unexpected translation served: {identity}"
        )
    missing = read_json(web + "/api/feed?q=codepick-no-result-20260917")
    require(
        missing["total"] == 0 and missing["items"] == [],
        "Empty search should not fall back to demo data",
    )
    page = read_json(web + "/api/feed?limit=2")
    require(len(page["items"]) == min(2, len(expected)), "Pagination limit ignored")
    if len(expected) > 2:
        require(bool(page["next_cursor"]), "Missing next page cursor")
        next_page = read_json(web + "/api/feed?limit=2&cursor=" + page["next_cursor"])
        require(
            not (
                {item["id"] for item in page["items"]}
                & {item["id"] for item in next_page["items"]}
            ),
            "Pagination repeats articles",
        )
    for base, suffix in ((web, "/zh"), (reader, "/docs"), (l2_api, "/docs")):
        with urlopen(base + "/", timeout=15) as response:
            require(
                response.status == 200 and urlparse(response.url).path == suffix,
                f"Root navigation failed: {base}",
            )
    try:
        urlopen(l2_api + "/content/999999999", timeout=15)
    except HTTPError as error:
        require(error.code == 404, "Unknown content should return 404")
    else:
        raise RuntimeError("Unknown content did not return 404")
    try:
        urlopen(
            Request(
                l0_api + "/api/crawl",
                data=b"{}",
                headers={"Content-Type": "application/json"},
            ),
            timeout=15,
        )
    except HTTPError as error:
        require(error.code == 403, "L0 preview write must be rejected")
    else:
        raise RuntimeError("Read-only L0 accepted a write")
    return {
        "status": "PASS",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_items": len(items),
        "readable_items": len(expected),
        "translations": 0,
        "processing": "extractive / heuristic; no model calls",
        "items": items,
        "checks": [
            "cross-layer source and version identity",
            "bounded literal excerpts",
            "L2 completed-only read",
            "L3 same-origin real feed and details",
            "empty search and pagination",
            "web/API root navigation",
            "unknown content 404",
            "L0 write rejected 403",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--web", default="http://127.0.0.1:13200")
    parser.add_argument("--l0", default="http://127.0.0.1:18000")
    parser.add_argument("--reader", default="http://127.0.0.1:18100")
    parser.add_argument("--l2", default="http://127.0.0.1:18230")
    args = parser.parse_args()
    report = verify(args.data_dir.resolve(), args.web, args.l0, args.l2, args.reader)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"CODEPICK REAL PREVIEW: PASS ({report['source_items']} imported; {report['readable_items']} readable)"
    )


if __name__ == "__main__":
    main()
