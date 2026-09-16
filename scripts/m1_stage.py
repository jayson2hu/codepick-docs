"""Internal stages of verify_m1.py; run with each repository's own interpreter."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape


MARKER = "CodePick M1 disposable integration fixture v1\n"
GRAPH = "m1.graph.v1"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read(root, name):
    return json.loads((root / f"{name}.json").read_text(encoding="utf-8"))


def save(root, name, payload):
    (root / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def engine_for(root, layer):
    from sqlalchemy import URL, create_engine
    return create_engine(URL.create("sqlite", database=str(root / f"{layer}.db")))


def ingest(root, project):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session
    from core_data.db.bootstrap import create_all
    from core_data.db.models import ContentItem, RawDocument
    from core_data.events.outbox import relay_once
    from core_data.ingest.pipeline import crawl_source
    from core_data.query.api import get_content
    from core_data.sources.repository import create_source
    from core_data.storage.object_store import FileObjectStore

    require(not (root / "l0.db").exists(), "Ingestion requires a new fixture database")
    article = root / "article.html"
    article.write_text(
        "<html><head><title>AI coding agents with durable data</title></head><body><article>"
        "<h1>AI coding agents with durable data</h1><p>AI developer tools require reliable "
        "content identities and a durable processing boundary. This reproducible LangGraph "
        "and SQLAlchemy example persists analysis before a separate process reads it. "
        "A retry must preserve the original article, summary, source and language. "
        "Restart verification checks actual stored rows and bilingual results.</p>"
        "</article></body></html>", encoding="utf-8",
    )
    feed = root / "feed.xml"
    feed.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        '<title>CodePick M1 blog</title><link>https://example.test</link>'
        '<description>Offline M1 fixture</description><item><title>AI coding agents with durable data</title>'
        f'<link>{escape(article.as_uri())}</link><guid>m1-durable-article</guid>'
        '</item></channel></rss>', encoding="utf-8",
    )
    engine = engine_for(root, "l0")
    try:
        create_all(engine)
        store = FileObjectStore(root / "objects")
        with Session(engine) as session:
            source = create_source(session, name="CodePick M1 blog", feed_url=feed.as_uri())
            stats = crawl_source(session, store, source)
            session.commit()
            require(stats["content"] == 1 and stats["failed"] == 0, f"L0 ingestion failed: {stats}")
            item = session.scalar(select(ContentItem))
            require(item is not None, "L0 content is missing")
            content = get_content(session, store, item.id)
            envelopes = []
            def publish(topic, payload, key):
                envelopes.append({"topic": topic, "payload": payload, "event_id": key})
            require(relay_once(session, publish) == 1, "Expected one ingested event")
            session.commit()
            require(type(envelopes[0]["payload"]["content_id"]) is int, "L0 integer ID contract changed")
            save(root, "l0-events", envelopes)
            return {
                "content_id": item.id, "source_id": source.id, "source": content.source.name,
                "title": content.title, "text_sha256": digest(content.clean_text), "status": item.status,
                "content_version": item.current_version,
                "raw_count": session.scalar(select(func.count()).select_from(RawDocument)),
                "event_count": len(envelopes),
            }
    finally:
        engine.dispose()


def l1_context(root):
    from core_data.storage.object_store import FileObjectStore
    from l1_data_processing.sql_store import SqlAlchemyEnrichmentStore
    l0_engine, l1_engine = engine_for(root, "l0"), engine_for(root, "l1")
    return l0_engine, l1_engine, FileObjectStore(root / "objects"), SqlAlchemyEnrichmentStore(l1_engine)


def enrich(root, project):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session
    from core_data.db.models import ContentItem, RawDocument
    from l1_data_processing.consumer import parse_content_ingested
    from l1_data_processing.durable import process_content
    from l1_data_processing.events import OutboxEvent
    from l1_data_processing.input import L0ContentProvider
    from l1_data_processing.llm import FakeLLM

    initial = read(root, "ingest")
    l0_engine, l1_engine, objects, store = l1_context(root)
    try:
        store.create_schema()
        envelope = read(root, "l0-events")[0]
        event = OutboxEvent(envelope["event_id"], envelope["topic"], str(initial["content_id"]), envelope["payload"])
        message = parse_content_ingested(event)
        llm = FakeLLM()
        with Session(l0_engine) as session:
            result = process_content(message.content_id, store=store, provider=L0ContentProvider.from_session(session, objects), llm=llm, graph_version=GRAPH)
            require(result.status == "WAIT_SCORE" and not result.replayed, "L1 did not produce a new successful analysis")
            row = store.get(message.content_id)
            require(row["schema_version"] == 1, "L1 snapshot schema version changed")
            require(row["analysis"]["content_id"] == message.content_id, "Analysis ID mismatch")
            require(digest(row["input_snapshot"]["body"]) == initial["text_sha256"], "Persisted body differs from L0")
            require(row["input_snapshot"]["metadata"]["source"]["name"] == initial["source"], "Source was lost")
            require(len(store.pending_events()) == 1, "Expected a durable analyzed event")
            require(session.get(ContentItem, initial["content_id"]).status == initial["status"], "L1 changed L0 status")
            require(session.scalar(select(func.count()).select_from(RawDocument)) == initial["raw_count"], "L1 changed raw data")
            return {
                "content_id": message.content_id, "run_id": result.run_id, "status": result.status,
                "summary": row["analysis"]["summary"], "base_tags": row["analysis"]["base_tags"],
                "lang": row["analysis"]["lang"], "text_sha256": initial["text_sha256"],
                "llm_calls": dict(llm.calls), "pending_events": 1,
            }
    finally:
        l0_engine.dispose()
        l1_engine.dispose()


def replay(root, project):
    from sqlalchemy.orm import Session
    from l1_data_processing.durable import process_content
    from l1_data_processing.input import L0ContentProvider
    from l1_data_processing.llm import FakeLLM

    initial = read(root, "enrich")
    l0_engine, l1_engine, objects, store = l1_context(root)
    try:
        llm = FakeLLM()
        with Session(l0_engine) as session:
            result = process_content(initial["content_id"], store=store, provider=L0ContentProvider.from_session(session, objects), llm=llm, graph_version=GRAPH)
        require(result.replayed and result.run_id == initial["run_id"] and not llm.calls, "Restarted L1 repeated processing")
        pending = store.pending_events()
        require(len(pending) == 1, "Duplicate delivery produced another event")
        def unavailable(topic, payload, event_id):
            raise ConnectionError("M1 simulated delivery outage")
        try:
            store.relay_once(unavailable)
        except ConnectionError:
            pass
        else:
            raise RuntimeError("Delivery failure was swallowed")
        require(len(store.pending_events()) == 1, "Failed delivery was marked sent")
        def persist_envelope(topic, payload, event_id):
            target = root / "l1-events.json"
            events = read(root, "l1-events") if target.exists() else []
            if not any(event["event_id"] == event_id for event in events):
                events.append({"topic": topic, "payload": payload, "event_id": event_id})
                save(root, "l1-events", events)
        require(store.relay_once(persist_envelope) == 1, "Pending event did not recover")
        require(not store.pending_events() and store.relay_once(persist_envelope) == 0, "Relay duplicate suppression failed")
        return {"run_id": result.run_id, "replayed": result.replayed, "llm_calls": dict(llm.calls), "failure_recovery": True, "delivered_events": len(read(root, "l1-events"))}
    finally:
        l0_engine.dispose()
        l1_engine.dispose()


def score(root, project):
    from judgment_graph.graph.build import run_content_pipeline
    from judgment_graph.input.sqlalchemy_provider import SqlAlchemyAnalysisProvider
    from judgment_graph.lens.loader import FileLensLoader
    from judgment_graph.llm import FakeLLM
    from judgment_graph.persist.sqlalchemy_repository import SqlAlchemyJudgmentRepository

    initial = read(root, "ingest")
    analyzed = read(root, "enrich")
    l1_engine, l2_engine = engine_for(root, "l1"), engine_for(root, "l2")
    try:
        envelope = read(root, "l1-events")[0]
        require(envelope["topic"] == "content.analyzed", "Wrong L1 event topic")
        content_id = int(envelope["payload"]["content_id"])
        require(content_id == initial["content_id"], "Event ID mismatch")
        provider = SqlAlchemyAnalysisProvider(l1_engine)
        analysis = provider.get(content_id)
        require(analysis.summary == analyzed["summary"] and analysis.tags == analyzed["base_tags"], "L2 lost actual L1 fields")
        require(analysis.language == analyzed["lang"] and analysis.source == initial["source"], "L2 lost language/source")
        require(digest(analysis.text) == initial["text_sha256"], "L2 did not read actual L0 body snapshot")
        repository = SqlAlchemyJudgmentRepository(l2_engine)
        repository.create_schema()
        lenses = FileLensLoader()
        repository.seed_lens(asdict(lenses.load_lens("ai-coding")))
        run_content_pipeline(content_id, "ai-coding", provider, lenses, FakeLLM(), repository)
        require(repository.get_status(content_id) == "COMPLETED", "L2 scoring did not complete")
        scores = repository.completed_scores("ai-coding")
        require(len(scores) == 1 and scores[0].content_id == content_id, "L2 score not persisted")
        for language in ("en", "zh"):
            require(repository.translation(content_id, language) is not None, f"Missing {language} translation")
        events = repository.outbox()
        require(len(events) == 1 and events[0].type == "content.completed", "L2 completion event is missing")
        return {"content_id": content_id, "status": "COMPLETED", "quality_score": scores[0].quality_score, "translations": ["en", "zh"], "completed_events": 1, "source": analysis.source, "text_sha256": digest(analysis.text)}
    finally:
        l1_engine.dispose()
        l2_engine.dispose()


def read_result(root, project):
    from judgment_graph.events.consume import EventConsumer
    from judgment_graph.graph.build import run_content_pipeline
    from judgment_graph.lens.loader import FileLensLoader
    from judgment_graph.persist.sqlalchemy_repository import SqlAlchemyJudgmentRepository
    initial = read(root, "score")
    engine = engine_for(root, "l2")
    try:
        repository = SqlAlchemyJudgmentRepository(engine)
        content_id = initial["content_id"]
        require(repository.get_status(content_id) == "COMPLETED", "Status was lost after process restart")
        scores = repository.completed_scores("ai-coding")
        require(len(scores) == 1 and scores[0].quality_score == initial["quality_score"], "Score visibility was lost after restart")
        for language in ("en", "zh"):
            require(repository.translation(content_id, language) is not None, "Translation lost after restart")
        require(len(repository.outbox()) == 1, "Completion event lost after restart")
        class NoCalls:
            def __getattr__(self, name):
                raise AssertionError(f"Completed content must not call provider/model again: {name}")
        provider, llm = NoCalls(), NoCalls()
        lenses = FileLensLoader()
        EventConsumer(provider, lenses, llm, repository).consume("content.analyzed", {"content_id": content_id})
        run_content_pipeline(content_id, "ai-coding", provider, lenses, llm, repository)
        require(len(repository.outbox()) == 1 and repository.get_status(content_id) == "COMPLETED", "Restart duplicate changed completion")
        return {"content_id": content_id, "status": "COMPLETED", "persistent_score": True, "persistent_translations": True, "persistent_outbox": True, "restart_duplicate_no_model_calls": True}
    finally:
        engine.dispose()


def update(root, project):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session
    from core_data.db.models import ContentItem, OutboxEvent, RawDocument, Source
    from core_data.ingest.pipeline import crawl_source
    from core_data.query.api import get_content
    from core_data.storage.object_store import FileObjectStore
    initial = read(root, "ingest")
    article = root / "article.html"
    article.write_text(article.read_text(encoding="utf-8").replace("</article>", "<p>This second revision adds a deterministic content-version check for reliable AI coding workers and durable event delivery.</p></article>"), encoding="utf-8")
    engine = engine_for(root, "l0")
    try:
        objects = FileObjectStore(root / "objects")
        with Session(engine) as session:
            source = session.get(Source, initial["source_id"])
            stats = crawl_source(session, objects, source)
            session.commit()
            require(stats["failed"] == 0, "L0 update failed")
            item = session.get(ContentItem, initial["content_id"])
            content = get_content(session, objects, item.id)
            require(item.current_version > initial["content_version"], "L0 content version did not change")
            require(digest(content.clean_text) != initial["text_sha256"], "Updated source text did not change")
            return {
                "content_id": item.id, "content_version": item.current_version, "text_sha256": digest(content.clean_text),
                "raw_count": session.scalar(select(func.count()).select_from(RawDocument)),
                "l0_event_rows": session.scalar(select(func.count()).select_from(OutboxEvent)),
                "trigger": "Explicit L1 reread; automatic L0 update notification is not implemented",
            }
    finally:
        engine.dispose()


def versions(root, project):
    from sqlalchemy.orm import Session
    from l1_data_processing.durable import process_content
    from l1_data_processing.input import L0ContentProvider
    from l1_data_processing.llm import FakeLLM
    initial = read(root, "enrich")
    updated = read(root, "update")
    l0_engine, l1_engine, objects, store = l1_context(root)
    try:
        with Session(l0_engine) as session:
            provider = L0ContentProvider.from_session(session, objects)
            def process(graph=GRAPH, key=None, llm=None):
                return process_content(initial["content_id"], store=store, provider=provider, llm=llm or FakeLLM(), graph_version=graph, reprocess_key=key)
            content_version = process()
            require(content_version.run_id != initial["run_id"] and not content_version.replayed, "Changed content was swallowed")
            row = store.get(initial["content_id"])
            require(digest(row["input_snapshot"]["body"]) == updated["text_sha256"], "L1 did not persist the changed article")
            duplicate_llm = FakeLLM()
            same = process(llm=duplicate_llm)
            require(same.replayed and not duplicate_llm.calls, "Repeated new content version was not idempotent")
            graph_version = process(graph="m1.graph.v2")
            forced = process(graph="m1.graph.v2", key="m1-force-request")
            retry_llm = FakeLLM()
            forced_retry = process(graph="m1.graph.v2", key="m1-force-request", llm=retry_llm)
            require(len({content_version.run_id, graph_version.run_id, forced.run_id}) == 3, "Version/reprocess requests did not get distinct identities")
            require(forced_retry.replayed and forced_retry.run_id == forced.run_id and not retry_llm.calls, "Retried force request was duplicated")
            events = store.pending_events()
            require(len(events) == 3 and len({event.event_id for event in events}) == 3, "Version notifications were lost or duplicated")
            return {"content_id": initial["content_id"], "content_update_notified": True, "graph_update_notified": True, "explicit_reprocess_notified": True, "repeat_request_idempotent": True, "new_pending_events": 3, "l2_version_rescoring": "Not exercised; M1 verifies the first successful version only"}
    finally:
        l0_engine.dispose()
        l1_engine.dispose()


def main():
    stages = {"ingest": ingest, "enrich": enrich, "replay": replay, "score": score, "read": read_result, "update": update, "versions": versions}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=stages)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    require((root / ".codepick-m1-fixture").read_text(encoding="utf-8") == MARKER, "Only a fresh M1 fixture directory may be used")
    payload = stages[args.stage](root, args.project_root.resolve())
    payload["stage"] = args.stage
    payload["status_check"] = "PASS"
    save(root, args.stage, payload)
    print(f"M1 {args.stage}: PASS")


if __name__ == "__main__":
    main()
