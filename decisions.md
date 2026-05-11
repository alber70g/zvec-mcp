# Decisions

## ADR-001: Build On `cluster2600/zvec-mcp`

### Problem

We need an MCP server for an existing markdown wiki. It should support vector
search through local embeddings and let the user navigate between documents by
wikilinks, backlinks, and source files.

The original plan was a new generic Bun/TypeScript MCP server with zvec-native
dense and BM25 sparse vectors. Research showed this would require implementing
substantial plumbing: file walking, chunking, embedding calls, zvec collection
management, MCP tools, reindexing, and wiki graph navigation.

### Alternatives

1. **Build a new TypeScript server from scratch.**
   - Pros: exact desired architecture, Streamable HTTP, generic corpus config.
   - Cons: most implementation work; repeats existing zvec and MCP plumbing.

2. **Adapt `@cosmiclasagnadev/zmem`.**
   - Pros: closest full document-search product; TypeScript, file walking,
     MCP, zvec dense retrieval, SQLite BM25.
   - Cons: not zvec-native for keyword/sparse search; memory-workspace product
     rather than a small zvec MCP extension.

3. **Adapt `zvec-ai/zvec-mcp-server`.**
   - Pros: comprehensive zvec MCP API with collection and multi-vector tools.
   - Cons: too low-level; no document tree ingestion or wiki navigation.

4. **Adapt `cluster2600/zvec-mcp`.**
   - Pros: already has the desired Python/FastMCP/zvec shape, HTTP embedding
     backend for LM Studio, single-file ingest, knowledge search, and memory
     tools.
   - Cons: currently lacks directory ingestion, markdown graph navigation, and
     dense+BM25 hybrid search.

### Chosen

Use `cluster2600/zvec-mcp` as the base and extend it.

### Reasoning

This choice avoids rebuilding the MCP, zvec, and LM Studio embedding plumbing.
It also keeps the first version small: add batch markdown ingestion and
wiki-navigation tools while preserving the existing knowledge search.

The tradeoff is deliberate. v1 will not implement zvec-native BM25 sparse
vectors or Streamable HTTP. Those remain future decisions after the core wiki
search and navigation loop is working.

### Consequences

- Runtime stays Python and FastMCP over stdio.
- Existing tools remain compatible.
- Wiki navigation is implemented as direct filesystem reads plus sidecar graph
  metadata, not as generated wiki edits.
- Future work can revisit zvec sparse/BM25 search once the first workflow is
  useful.

## ADR-002: Add New Batch Ingest Tool Instead Of Overloading File Ingest

### Problem

The existing `knowledge_ingest_file(path)` tool ingests one file. We need to
ingest an existing wiki tree using a root path and glob pattern.

### Alternatives

1. Extend `knowledge_ingest_file` with path/glob behavior.
2. Add a new `knowledge_ingest_path` tool.

### Chosen

Add `knowledge_ingest_path`.

### Reasoning

Keeping single-file ingest unchanged lowers regression risk and keeps the MCP
tool semantics clear. Batch ingestion has different error reporting, traversal,
and safety needs, so it should be its own tool.

## ADR-003: Navigation Reads Markdown Directly

### Problem

Search returns chunks from zvec, but navigation needs whole documents and graph
relationships such as wikilinks and backlinks.

### Alternatives

1. Store complete markdown documents inside zvec fields.
2. Store navigation metadata in zvec.
3. Read markdown directly from disk and keep a small sidecar graph index.

### Chosen

Read markdown directly from disk and use sidecar graph metadata.

### Reasoning

The wiki already exists on disk and must remain the source of truth. Direct
reads avoid duplicating large markdown bodies in zvec and keep navigation fresh
when a user asks for a specific file. The sidecar index only accelerates
backlinks and can be rebuilt.

For the notes wiki, existing `wiki/_backlinks.json` should be preferred when it
is present because it already encodes the wiki's stage-2 backlink conventions.

## ADR-004: Keep v1 Semantic Search Dense-Only

### Problem

The target retrieval stack may eventually need dense vector search plus BM25
keyword search with weighted fusion. This fork currently has dense zvec search
only.

### Alternatives

1. Add zvec sparse/BM25 vectors now.
2. Add SQLite FTS5/BM25 now and fuse outside zvec.
3. Keep v1 search dense-only and focus on existing-document ingestion plus wiki
   navigation.

### Chosen

Keep v1 search dense-only.

### Reasoning

Directory ingestion and wiki navigation are the immediate missing capabilities.
Adding hybrid search now would change zvec schema, ingestion, query behavior,
and tests at the same time. Keeping search dense-only preserves the upstream
behavior and gives us a verified baseline before changing retrieval quality.

### Consequences

- `knowledge_search` remains semantic vector search only.
- Exact keyword/BM25 behavior is deferred.
- Future hybrid search can be evaluated against the current test suite and
  smoke workflow.

## ADR-005: Default HTTP Embeddings To Local Qwen3 In LM Studio

### Problem

The upstream project defaulted HTTP embeddings to a Nomic model. The desired
local setup is LM Studio on `http://127.0.0.1:1234/v1/embeddings` with
`text-embedding-qwen3-embedding-0.6b`.

### Alternatives

1. Keep upstream Nomic defaults and document Qwen3 as an override.
2. Change defaults to Qwen3 and keep all values environment-configurable.

### Chosen

Change defaults to Qwen3 and keep environment overrides.

### Reasoning

This fork is currently being shaped around the local notes wiki workflow. A
default that matches the actual expected LM Studio model reduces setup friction,
while environment variables still allow other embedding servers and models.

### Consequences

- Default `ZVEC_MCP_HTTP_MODEL` is `text-embedding-qwen3-embedding-0.6b`.
- Default `ZVEC_MCP_HTTP_DIM` is `1024`.
- Existing users of other HTTP models must set env vars explicitly.

## ADR-006: Docker Image Uses HTTP Embeddings By Default

### Problem

The notes wiki MCP server should run as a Docker container, but a default Python
install that includes local sentence-transformer embeddings pulls in PyTorch and
large GPU dependencies. The intended notes workflow uses LM Studio through an
OpenAI-compatible HTTP embedding endpoint.

### Alternatives

1. Keep `sentence-transformers` as a required dependency.
2. Build a separate Docker-only requirements set.
3. Make local sentence-transformer embeddings an optional package extra and let
   the Docker image install the core package.

### Chosen

Make local embeddings optional with `zvec-mcp[local]` and have Docker install the
core package configured for HTTP embeddings.

### Reasoning

The core MCP server, zvec storage, HTTP embeddings, path ingestion, and wiki
navigation do not require PyTorch. Keeping the default container small makes it
usable as an MCP sidecar for the notes repository. Users who need fully offline
local embeddings can still install the `local` extra outside Docker or build a
custom image.

### Consequences

- The Docker image defaults to `ZVEC_MCP_EMBEDDING=http`.
- `pip install zvec-mcp` no longer installs sentence-transformers.
- `pip install "zvec-mcp[local]"` is required for the `local` backend.
