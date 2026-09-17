# 2026-09-17 本轮修改文件清单

按五仓库开始时的 main 基线至本轮交付生成，包含新增源码、测试、文档和配置。原文、数据库、令牌、日志、依赖和构建产物不在清单内。验收与剩余项见 [本轮记录](../PRODUCT_ACCEPTANCE_2026-09-17.md)。

## codepick-docs

```text
DEVELOPMENT_PLAN.md
LOCAL_DEVELOPMENT.md
PRODUCT_ACCEPTANCE_2026-09-17.md
PRODUCT_REBUILD_PLAN.md
PRODUCT_REVIEW_2026-09-17.md
PROJECT_STATUS.md
README.md
REAL_CONTENT_PREVIEW.md
UBUNTU_LOCAL_DEVELOPMENT.md
contracts/L1-L2-v1.md
scripts/run_preview.py
scripts/test_run_preview.py
scripts/verify_preview_recovery.mjs
scripts/verify_real_preview.py
verification/2026-09-17-changed-files.md
```

## deepdata

```text
DEVELOPMENT.md
README.md
deploy/real-preview-sources.json
docs/2026-09-17-readonly-dashboard.md
docs/2026-09-17-real-public-preview.md
src/core_data/ingest/adapters/rss.py
src/core_data/ingest/extractor.py
src/core_data/ingest/fetcher.py
src/core_data/ingest/pipeline.py
src/core_data/ingest/rss.py
src/core_data/query/api.py
src/core_data/query/contracts.py
src/core_data/scripts/dashboard.html
src/core_data/scripts/dashboard.py
src/core_data/scripts/real_preview.py
tests/unit/test_adapters.py
tests/unit/test_dashboard_readonly.py
tests/unit/test_failure_paths.py
tests/unit/test_pipeline_contract.py
```

## seek_data

```text
DEVELOPMENT.md
README.md
docs/2026-09-17-extractive-public-preview.md
src/l1_data_processing/graph.py
src/l1_data_processing/input/l0.py
src/l1_data_processing/llm/__init__.py
src/l1_data_processing/llm/extractive.py
src/l1_data_processing/real_preview.py
src/l1_data_processing/schema.py
src/l1_data_processing/tagging.py
tests/test_base_analysis_schema.py
tests/test_extractive.py
tests/test_l0_provider.py
tests/test_tagging.py
```

## agentic

```text
README.md
docs/2026-09-17-real-content-preview.md
docs/2026-09-17-versioned-read-consistency.md
packages/judgment_graph/judgment_graph/graph/langgraph_build.py
packages/judgment_graph/judgment_graph/graph/scoring.py
packages/judgment_graph/judgment_graph/graph/translate.py
packages/judgment_graph/judgment_graph/heuristic.py
packages/judgment_graph/judgment_graph/http_api.py
packages/judgment_graph/judgment_graph/input/provider.py
packages/judgment_graph/judgment_graph/input/sqlalchemy_provider.py
packages/judgment_graph/judgment_graph/llm.py
packages/judgment_graph/judgment_graph/persist/contracts.py
packages/judgment_graph/judgment_graph/persist/repository.py
packages/judgment_graph/judgment_graph/persist/sqlalchemy_repository.py
packages/judgment_graph/judgment_graph/review/queue.py
packages/judgment_graph/judgment_graph/scripts/prepare_preview.py
packages/judgment_graph/judgment_graph/workers/scoring/worker.py
packages/judgment_graph/tests/test_http_schema_validation.py
packages/judgment_graph/tests/test_http_version_consistency.py
packages/judgment_graph/tests/test_preview_safety.py
packages/judgment_graph/tests/test_real_preview.py
packages/judgment_graph/tests/test_versioned_documents.py
```

## pickblog

```text
DEVELOPMENT.md
README.md
apps/reader-web/.gitignore
apps/reader-web/UX_REDESIGN.md
apps/reader-web/app/[locale]/brief/page.tsx
apps/reader-web/app/[locale]/developers/page.tsx
apps/reader-web/app/[locale]/error.tsx
apps/reader-web/app/[locale]/items/[id]/page.tsx
apps/reader-web/app/[locale]/layout.tsx
apps/reader-web/app/[locale]/library/page.tsx
apps/reader-web/app/[locale]/login/page.tsx
apps/reader-web/app/[locale]/not-found.tsx
apps/reader-web/app/[locale]/page.tsx
apps/reader-web/app/[locale]/pricing/page.tsx
apps/reader-web/app/globals.css
apps/reader-web/app/sitemap.ts
apps/reader-web/components/AccountMenu.tsx
apps/reader-web/components/ApiKeyPanel.tsx
apps/reader-web/components/ApiUsageChart.tsx
apps/reader-web/components/BilingualBody.tsx
apps/reader-web/components/BillingPanel.tsx
apps/reader-web/components/BriefGate.tsx
apps/reader-web/components/CompanionWidget.tsx
apps/reader-web/components/ContentCard.tsx
apps/reader-web/components/FeedFilters.tsx
apps/reader-web/components/Header.tsx
apps/reader-web/components/InterestOnboarding.tsx
apps/reader-web/components/LoadMore.tsx
apps/reader-web/components/LoginForm.tsx
apps/reader-web/components/ProvenanceStrip.tsx
apps/reader-web/components/ReadingActions.tsx
apps/reader-web/components/SaveLaterButton.tsx
apps/reader-web/components/SavedLibrary.tsx
apps/reader-web/components/ScoreExplainer.tsx
apps/reader-web/components/Sidebar.tsx
apps/reader-web/components/TrackedContentLink.tsx
apps/reader-web/components/admin/AdminTaxonomyPanel.tsx
apps/reader-web/lib/api.ts
apps/reader-web/lib/client-api.ts
apps/reader-web/lib/locale.ts
apps/reader-web/lib/presentation.ts
apps/reader-web/lib/saved.ts
apps/reader-web/lib/session.ts
apps/reader-web/m2-tests/reader-development-account.spec.ts
apps/reader-web/m2-tests/reader-m1-fake.spec.ts
apps/reader-web/m2-tests/reader-real.spec.ts
apps/reader-web/m2-tests/reader-upstream-error.spec.ts
apps/reader-web/next.config.mjs
apps/reader-web/tests/reader.spec.ts
db/alembic/versions/0003_sqlite_generated_ids.py
docs/2026-09-17-real-content-preview.md
services/public-api/public_api/main.py
services/reader-api/reader_api/main.py
services/reader-api/reader_api/routers/companion.py
services/reader-api/reader_api/routers/feed.py
services/reader-api/reader_api/routers/me.py
services/shared/codepick_l3/provider.py
services/shared/codepick_l3/public_contract.py
services/shared/codepick_l3/repository.py
services/shared/codepick_l3/schemas.py
tests/test_companion_failure_boundary.py
tests/test_content_provenance.py
tests/test_l3_contracts.py
tests/test_reader_discovery.py
tests/test_sqlite_generated_ids.py
```
