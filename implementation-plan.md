# Implementation Plan: Wiki-Aware zvec-mcp

## Goal

Extend this fork of `cluster2600/zvec-mcp` into a wiki-aware MCP server for an
existing Obsidian-style markdown knowledge base.

The first target corpus is:

```text
/Users/albert/projects/alber70g/notes/wiki
```

The implementation should preserve the upstream shape: Python, FastMCP over
stdio, zvec storage, and HTTP embeddings through LM Studio.

## Success Criteria

- A user can ingest an existing markdown tree with one MCP tool call.
- Search results still use the existing zvec-backed `knowledge_search` flow.
- A user can navigate from a searched source file to its outgoing wikilinks and
  backlinks.
- Wiki navigation reads markdown files directly from disk and never edits them.
- The implementation remains compatible with the existing single-file ingest
  and memory tools.

## Scope

### In Scope

- Add batch path ingestion for existing documents.
- Add markdown/Obsidian link parsing.
- Add direct retrieval of wikilink targets.
- Add backlink retrieval from a sidecar navigation index, with special support
  for an existing `wiki/_backlinks.json` file when present.
- Add tests for path walking, wikilink resolution, and navigation behavior.
- Update README usage examples for the notes wiki and LM Studio embedding model.

### Out of Scope for v1

- Streamable HTTP transport.
- zvec-native BM25 sparse vectors and weighted dense/BM25 fusion.
- Generic multi-corpus config files.
- Editing wiki markdown.
- Rewriting chunking to be heading-aware.
- Automatic file watching.

## Proposed Tools

### `knowledge_ingest_path`

Arguments:

- `root: str`
- `glob_pattern: str = "**/*.md"`
- `exclude_patterns: list[str] | None = None`
- `max_files: int | None = None`

Behavior:

- Resolve `root` to an absolute path.
- Refuse non-directories.
- Walk only files under `root`.
- Match files with `Path.rglob`/`fnmatch`; avoid adding a new dependency unless
  the stdlib version becomes awkward.
- Default excludes should skip hidden directories, `.git`, `.obsidian`, and
  generated index JSON when matching markdown is broadened later.
- Call existing `KnowledgeBase.ingest_file` for each file.
- Return JSON with `root`, `glob_pattern`, `files_seen`, `files_ingested`,
  `chunks_stored`, and per-file failures.
- Rebuild the navigation sidecar after successful ingestion.

### `knowledge_navigate_file`

Arguments:

- `source_file: str`

Behavior:

- Resolve the file path.
- Read the file from disk.
- Return outgoing wikilinks, resolved target paths, missing targets, backlinks,
  and whether each target exists.
- If `source_file` is inside a wiki root containing `_backlinks.json`, use that
  file as the preferred backlink source.
- Otherwise use the generated sidecar navigation index.

### `knowledge_wikilink_retrieve`

Arguments:

- `source_file: str`
- `target_link: str`

Behavior:

- Parse `target_link` as an Obsidian wikilink target, allowing raw targets like
  `people/randy-daal`, `[[people/randy-daal]]`, and
  `[[people/randy-daal|Randy]]`.
- Resolve relative to the source file first.
- If not found, resolve from the nearest wiki root.
- Add `.md` when the target has no extension.
- If the target ends in `/`, resolve to `index.md`.
- Return the resolved path, existence status, and markdown content when found.

### `knowledge_backlinks`

Arguments:

- `source_file: str`

Behavior:

- Return files that reference `source_file`.
- Use `wiki/_backlinks.json` when available.
- Fall back to the generated sidecar navigation index.

## Implementation Steps

1. Add `src/zvec_mcp/wiki.py`.
   - Include `extract_wikilinks`, `normalize_wikilink_target`,
     `resolve_wikilink`, `build_navigation_index`, and backlink helpers.
   - Keep this module read-only with respect to wiki markdown.

2. Extend `KnowledgeBase`.
   - Add `ingest_path`.
   - Add a small navigation-index rebuild call for markdown trees.
   - Keep `ingest_file` unchanged for single-file behavior.

3. Extend `server.py`.
   - Register the four new tools.
   - Return JSON strings matching existing tool style.
   - Catch file/path errors and report structured error JSON.

4. Add tests.
   - Add pytest tests for wikilink parsing and resolution.
   - Add a temporary markdown tree test for `knowledge_ingest_path`.
   - Use a fake embedder so tests do not require LM Studio.
   - Use temporary zvec data directories.

5. Update docs.
   - Document LM Studio defaults for
     `text-embedding-qwen3-embedding-0.6b`.
   - Add notes-wiki ingestion and navigation examples.

## Verification

- `python -m compileall -q src`
- `uv run --python 3.12 pytest`
- Manual smoke test against a tiny temporary markdown tree:
  - ingest path
  - search
  - navigate a file
  - retrieve a wikilink target
  - read backlinks

