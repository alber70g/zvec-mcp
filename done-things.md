# Done Things

## Completed

- Forked `cluster2600/zvec-mcp` to `alber70g/zvec-mcp`.
- Cloned the fork to `/Users/albert/projects/alber70g/zvec-mcp`.
- Confirmed remotes:
  - `origin`: `git@github.com:alber70g/zvec-mcp.git`
  - `upstream`: `git@github.com:cluster2600/zvec-mcp.git`
- Inspected the upstream project shape:
  - `src/zvec_mcp/server.py`
  - `src/zvec_mcp/knowledge.py`
  - `src/zvec_mcp/embeddings.py`
  - `src/zvec_mcp/config.py`
  - `src/zvec_mcp/memory.py`
- Indexed the fork with code-review-graph.
- Ran baseline static compilation with `python3 -m compileall -q src`.
- Added this implementation ledger.
- Added `implementation-plan.md`.
- Added `decisions.md`.
- Added milestone plans `m1.md`, `m2.md`, `m3.md`, and `m4.md`.
- Added `src/zvec_mcp/wiki.py` for read-only wikilink parsing, target
  resolution, sidecar navigation indexes, and backlink lookup.
- Added `KnowledgeBase.ingest_path`.
- Added MCP tools:
  - `knowledge_ingest_path`
  - `knowledge_navigate_file`
  - `knowledge_wikilink_retrieve`
  - `knowledge_backlinks`
- Changed HTTP embedding defaults to LM Studio Qwen3:
  - `ZVEC_MCP_HTTP_MODEL=text-embedding-qwen3-embedding-0.6b`
  - `ZVEC_MCP_HTTP_DIM=1024`
- Added pytest configuration for the `src/` layout.
- Added tests for wiki parsing, navigation, path ingestion, MCP wrappers, and
  a local smoke workflow.
- Updated README with wiki ingestion and navigation examples.
- Added Docker support for running the MCP server over stdio:
  - `Dockerfile`
  - `.dockerignore`
  - `docker-compose.example.yml`
- Made `sentence-transformers` an optional `local` extra so the default Docker
  image can use HTTP embeddings without installing PyTorch.

## Implementation Tasks

- [x] Add `src/zvec_mcp/wiki.py` with wikilink parsing, target resolution, and
      backlink helpers.
- [x] Add `KnowledgeBase.ingest_path`.
- [x] Add `knowledge_ingest_path` MCP tool.
- [x] Add `knowledge_navigate_file` MCP tool.
- [x] Add `knowledge_wikilink_retrieve` MCP tool.
- [x] Add `knowledge_backlinks` MCP tool.
- [x] Add pytest coverage for wiki parsing and navigation.
- [x] Add pytest coverage for path ingestion with a fake embedder.
- [x] Update README with notes-wiki and LM Studio examples.
- [x] Add Docker support for stdio MCP usage.
- [x] Keep local embedding dependencies out of the default Docker image.
- [x] Run full verification.

## ADR Log

- ADR-001: Build on `cluster2600/zvec-mcp`.
- ADR-002: Add new batch ingest tool instead of overloading file ingest.
- ADR-003: Navigation reads markdown directly.
- ADR-004: Keep v1 semantic search dense-only.
- ADR-005: Default HTTP embeddings to local Qwen3 in LM Studio.
- ADR-006: Docker image uses HTTP embeddings by default.

## Validation Log

- `python3 -m compileall -q src` passed before planning-doc changes.
- `uv run --python 3.12 python -m compileall -q src` passed after creating
  the local `.venv` and installing project dependencies.
- `uv run --python 3.12 pytest -q` found no tests in the current fork.
- `uv run --python 3.12 python -m compileall -q src tests` passed after
  implementation.
- `uv run --python 3.12 --extra dev python -m pytest -q` passed with 11 tests.
- Smoke coverage in `tests/test_wiki_smoke.py` verifies path ingest, search,
  navigation, wikilink retrieval, and backlinks with a fake embedder.
- `docker build --no-cache -t zvec-mcp:local .` passed after moving
  sentence-transformers to the optional `local` extra.
- `docker image inspect zvec-mcp:local` confirmed the `zvec-mcp` entrypoint and
  a 443756721-byte image.
