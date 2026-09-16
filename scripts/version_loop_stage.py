"""Internal stages for the Redis-backed version event loop acceptance."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from xml.sax.saxutils import escape


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def engine_for(root: Path, layer: str):
    from sqlalchemy import URL, create_engine

    return create_engine(URL.create("sqlite", database=str(root / f"{layer}.db")))


def save(root: Path, name: str, value: dict[str, object]) -> None:
    (root / f"{name}.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def flush_redis(root: Path, redis_url: str, l0_queue: str, l1_queue: str) -> None:
    del root, l0_queue, l1_queue
    from redis import Redis

    Redis.from_url(redis_url).flushdb()


def seed(root: Path, redis_url: str, l0_queue: str, l1_queue: str) -> None:
    del l1_queue
    from redis import Redis
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    from core_data.db.bootstrap import create_all
    from core_data.db.models import ContentItem
    from core_data.events.outbox import relay_once
    from core_data.events.publishers import RedisStreamPublisher
    from core_data.ingest.pipeline import crawl_source
    from core_data.sources.repository import create_source
    from core_data.storage.object_store import FileObjectStore

    article = root / "article.html"
    article.write_text(
        "<html><head><title>Versioned CodePick article</title></head>"
        "<body><article><h1>Versioned CodePick article</h1>"
        "<p>Version one proves durable event delivery from L0 through L2.</p>"
        "</article></body></html>",
        encoding="utf-8",
    )
    feed = root / "feed.xml"
    feed.write_text(
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<title>Version loop</title><link>https://example.test</link>"
        "<description>Version loop fixture</description><item>"
        "<title>Versioned CodePick article</title>"
        f"<link>{escape(article.as_uri())}</link><guid>version-loop</guid>"
        "</item></channel></rss>",
        encoding="utf-8",
    )
    engine = engine_for(root, "l0")
    try:
        create_all(engine)
        with Session(engine) as session:
            source = create_source(
                session, name="Version loop", feed_url=feed.as_uri()
            )
            stats = crawl_source(
                session, FileObjectStore(root / "objects"), source
            )
            session.commit()
            require(stats["content"] == 1, f"unexpected L0 stats: {stats}")
            item = session.scalar(select(ContentItem))
            require(item is not None, "L0 content was not created")
            publisher = RedisStreamPublisher(
                Redis.from_url(redis_url, decode_responses=True),
                queue_name=l0_queue,
                key_prefix=f"{l0_queue}:published",
            )
            require(relay_once(session, publisher) == 1, "v1 event was not relayed")
            session.commit()
            save(root, "seed", {
                "content_id": item.id,
                "source_id": source.id,
                "content_version": item.current_version,
            })
    finally:
        engine.dispose()


def update(root: Path, redis_url: str, l0_queue: str, l1_queue: str) -> None:
    del l1_queue
    from redis import Redis
    from sqlalchemy.orm import Session

    from core_data.db.models import ContentItem, Source
    from core_data.events.outbox import relay_once
    from core_data.events.publishers import RedisStreamPublisher
    from core_data.ingest.pipeline import crawl_source
    from core_data.storage.object_store import FileObjectStore

    seed_result = json.loads((root / "seed.json").read_text(encoding="utf-8"))
    article = root / "article.html"
    article.write_text(
        article.read_text(encoding="utf-8").replace(
            "</article>",
            "<p>Version two must trigger L1 and L2 reprocessing automatically.</p>"
            "</article>",
        ),
        encoding="utf-8",
    )
    engine = engine_for(root, "l0")
    try:
        with Session(engine) as session:
            source = session.get(Source, seed_result["source_id"])
            stats = crawl_source(
                session, FileObjectStore(root / "objects"), source
            )
            session.commit()
            item = session.get(ContentItem, seed_result["content_id"])
            require(item is not None, "updated content disappeared")
            require(item.current_version == 2, "L0 did not create version 2")
            publisher = RedisStreamPublisher(
                Redis.from_url(redis_url, decode_responses=True),
                queue_name=l0_queue,
                key_prefix=f"{l0_queue}:published",
            )
            require(relay_once(session, publisher) == 1, "v2 event was not relayed")
            session.commit()
            save(root, "update", {
                "content_id": item.id,
                "content_version": item.current_version,
                "stats": stats,
            })
    finally:
        engine.dispose()


def prepare_l2(root: Path, redis_url: str, l0_queue: str, l1_queue: str) -> None:
    del redis_url, l0_queue, l1_queue
    from judgment_graph.lens.loader import FileLensLoader
    from judgment_graph.persist.sqlalchemy_repository import (
        SqlAlchemyJudgmentRepository,
    )

    engine = engine_for(root, "l2")
    try:
        repository = SqlAlchemyJudgmentRepository(engine)
        repository.create_schema()
        repository.seed_lens(
            asdict(FileLensLoader().load_lens("ai-coding"))
        )
    finally:
        engine.dispose()


def replay_stale(
    root: Path, redis_url: str, l0_queue: str, l1_queue: str
) -> None:
    del l0_queue
    from redis import Redis
    from sqlalchemy import MetaData, Table, select

    engine = engine_for(root, "l1")
    try:
        table = Table(
            "l1_outbox_events", MetaData(), autoload_with=engine
        )
        with engine.connect() as connection:
            row = connection.execute(
                select(table).order_by(table.c.created_at, table.c.event_id)
            ).mappings().first()
        require(row is not None, "L1 outbox is empty")
        envelope = json.dumps({
            "topic": row["topic"],
            "payload": row["payload"],
            "idempotency_key": row["event_id"],
        }, ensure_ascii=False, sort_keys=True)
        Redis.from_url(redis_url, decode_responses=True).rpush(
            l1_queue, envelope
        )
    finally:
        engine.dispose()


def verify(
    root: Path,
    redis_url: str,
    l0_queue: str,
    l1_queue: str,
    *,
    expected_revision: int,
    expected_events: int,
) -> None:
    del redis_url, l0_queue, l1_queue
    from judgment_graph.persist import models
    from judgment_graph.persist.sqlalchemy_repository import (
        SqlAlchemyJudgmentRepository,
    )
    from sqlalchemy import select

    seed_result = json.loads((root / "seed.json").read_text(encoding="utf-8"))
    content_id = int(seed_result["content_id"])
    engine = engine_for(root, "l2")
    try:
        repository = SqlAlchemyJudgmentRepository(engine)
        require(
            repository.get_status(content_id) == "COMPLETED",
            "L2 did not complete the current revision",
        )
        with engine.connect() as connection:
            state = connection.execute(
                select(models.content_judgment_state).where(
                    models.content_judgment_state.c.content_id == content_id
                )
            ).mappings().one()
        require(
            state["source_revision"] == expected_revision,
            f"expected L2 revision {expected_revision}, got {state['source_revision']}",
        )
        events = repository.outbox()
        require(
            len(events) == expected_events,
            f"expected {expected_events} completion events, got {len(events)}",
        )
        require(
            events[-1].payload["source_revision"] == expected_revision,
            "completion event revision does not match L2 state",
        )
        require(
            len(repository.completed_scores("ai-coding")) == 1,
            "current score is not visible",
        )
        save(root, f"verify-v{expected_revision}", {
            "content_id": content_id,
            "source_revision": expected_revision,
            "completion_events": expected_events,
            "status": "COMPLETED",
        })
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=[
            "flush",
            "seed",
            "update",
            "prepare-l2",
            "replay-stale",
            "verify",
        ],
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--redis-url", required=True)
    parser.add_argument("--l0-queue", required=True)
    parser.add_argument("--l1-queue", required=True)
    parser.add_argument("--expected-revision", type=int)
    parser.add_argument("--expected-events", type=int)
    args = parser.parse_args()
    kwargs = {
        "root": args.data_dir.resolve(),
        "redis_url": args.redis_url,
        "l0_queue": args.l0_queue,
        "l1_queue": args.l1_queue,
    }
    if args.stage == "verify":
        require(args.expected_revision is not None, "expected revision is required")
        require(args.expected_events is not None, "expected event count is required")
        verify(
            **kwargs,
            expected_revision=args.expected_revision,
            expected_events=args.expected_events,
        )
    else:
        {
            "flush": flush_redis,
            "seed": seed,
            "update": update,
            "prepare-l2": prepare_l2,
            "replay-stale": replay_stale,
        }[args.stage](**kwargs)
    print(f"VERSION LOOP {args.stage}: PASS")


if __name__ == "__main__":
    main()
