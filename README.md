# zvec-mcp

Claude Code MCP server that gives your AI agent a **local vector database** for RAG knowledge retrieval and long-term memory — powered by [zvec](https://github.com/alibaba/zvec).

---

## Table of contents

- [What it does](#what-it-does)
- [Installation](#installation)
  - [Option A — Desktop extension (.mcpb)](#option-a--desktop-extension-mcpb)
  - [Option B — pip install](#option-b--pip-install)
  - [Option C — From source](#option-c--from-source)
- [Registering with Claude Code](#registering-with-claude-code)
  - [User scope](#user-scope-available-in-all-projects)
  - [Project scope](#project-scope-shared-via-mcpjson)
  - [Verify](#verify)
- [Embedding backends](#embedding-backends)
  - [HTTP — LM Studio / Ollama / vLLM](#http--lm-studio--ollama--vllm)
  - [Local — sentence-transformers](#local--sentence-transformers)
  - [OpenAI](#openai)
- [Configuration reference](#configuration-reference)
- [Tools reference](#tools-reference)
  - [Knowledge base (RAG)](#knowledge-base-rag)
  - [Memory](#memory)
  - [Status](#status)
- [Usage examples](#usage-examples)
- [Docker](#docker)
- [Architecture](#architecture)
- [Data storage](#data-storage)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## What it does

zvec-mcp runs as a [Model Context Protocol](https://modelcontextprotocol.io/) server over stdio. Once connected, Claude Code gets **11 new tools** for storing, searching, and managing a local vector database — completely offline, no data leaves your machine.

---

## Installation

### Prerequisites

- Python 3.10 or later
- macOS, Linux, or Windows
- An embedding source (one of):
  - A local server like [LM Studio](https://lmstudio.ai/), [Ollama](https://ollama.com/), or [vLLM](https://docs.vllm.ai/) (recommended)
  - [sentence-transformers](https://www.sbert.net/) installed locally
  - An [OpenAI](https://platform.openai.com/) API key

### Option A — Desktop extension (.mcpb)

The fastest way to get started. Download the pre-built `.mcpb` file and drag it into Claude Code.

1. Download `zvec-mcp-0.1.0.mcpb` from the [latest release](https://github.com/cluster2600/zvec-mcp/releases/latest)
2. Open Claude Code
3. Go to the **Extensions** tab
4. Drag the `.mcpb` file into the drop zone
5. Configure your embedding backend in the settings that appear

> **Note:** The `.mcpb` bundle defaults to the **HTTP** embedding backend and does not include sentence-transformers. To use local embeddings, install via pip instead (Option B).

### Option B — pip install

```bash
pip install zvec-mcp
```

This installs the `zvec-mcp` command-line entry point. To also get local offline embeddings:

```bash
pip install "zvec-mcp[local]"
```

For OpenAI embeddings:

```bash
pip install "zvec-mcp[openai]"
```

### Option C — From source

```bash
git clone https://github.com/cluster2600/zvec-mcp.git
cd zvec-mcp

# Create a virtual environment and install
uv venv --python 3.10
uv pip install -e .

# Optional: local embeddings
uv pip install -e ".[local]"

# Optional: OpenAI embeddings
uv pip install openai
```

---

## Registering with Claude Code

After installing, you need to tell Claude Code where to find the server.

### User scope (available in all projects)

```bash
claude mcp add-json zvec-mcp \
  '{"type":"stdio","command":"zvec-mcp","args":[],"env":{"ZVEC_MCP_DATA_DIR":"'"$HOME"'/.zvec-mcp","ZVEC_MCP_EMBEDDING":"http"}}' \
  --scope user
```

If you installed from source, use the full path to the venv binary:

```bash
claude mcp add-json zvec-mcp \
  '{"type":"stdio","command":"'"$(pwd)"'/.venv/bin/zvec-mcp","args":[],"env":{"ZVEC_MCP_DATA_DIR":"'"$HOME"'/.zvec-mcp","ZVEC_MCP_EMBEDDING":"http"}}' \
  --scope user
```

### Project scope (shared via `.mcp.json`)

Create or edit `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "zvec-mcp": {
      "command": "zvec-mcp",
      "args": [],
      "env": {
        "ZVEC_MCP_DATA_DIR": "${HOME}/.zvec-mcp",
        "ZVEC_MCP_EMBEDDING": "http",
        "ZVEC_MCP_HTTP_URL": "http://127.0.0.1:1234/v1/embeddings",
        "ZVEC_MCP_HTTP_MODEL": "text-embedding-qwen3-embedding-0.6b",
        "ZVEC_MCP_HTTP_DIM": "1024"
      }
    }
  }
}
```

> Replace `"zvec-mcp"` with the full path if the command is not on your `PATH` (e.g. `/path/to/zvec-mcp/.venv/bin/zvec-mcp`).

### Verify

```bash
claude mcp list
# zvec-mcp: zvec-mcp  - ✓ Connected
```

You can also check from inside Claude Code by asking:

> "What's the status of zvec-mcp?"

Claude will call the `zvec_status` tool and display the backend, dimensions, and collection stats.

---

## Embedding backends

zvec-mcp supports three embedding backends. You choose one via the `ZVEC_MCP_EMBEDDING` environment variable.

### HTTP — LM Studio / Ollama / vLLM

Calls any OpenAI-compatible `/v1/embeddings` endpoint. This is the **recommended** setup — it keeps embeddings local, runs on GPU if available, and requires no heavy Python dependencies (uses Python's built-in `urllib`).

**Setup with LM Studio:**

1. Install [LM Studio](https://lmstudio.ai/)
2. Download an embedding model (e.g. `text-embedding-qwen3-embedding-0.6b`)
3. Start the local server (LM Studio → Developer → Start Server)
4. Note the port (default `1234`) and API key if you enabled authentication

```json
{
  "mcpServers": {
    "zvec-mcp": {
      "command": "zvec-mcp",
      "args": [],
      "env": {
        "ZVEC_MCP_EMBEDDING": "http",
        "ZVEC_MCP_HTTP_URL": "http://127.0.0.1:1234/v1/embeddings",
        "ZVEC_MCP_HTTP_MODEL": "text-embedding-qwen3-embedding-0.6b",
        "ZVEC_MCP_HTTP_API_KEY": "your-api-key",
        "ZVEC_MCP_HTTP_DIM": "1024"
      }
    }
  }
}
```

**Setup with Ollama:**

1. Install [Ollama](https://ollama.com/)
2. Pull an embedding model: `ollama pull nomic-embed-text`
3. Ollama serves on port `11434` by default

```json
{
  "env": {
    "ZVEC_MCP_EMBEDDING": "http",
    "ZVEC_MCP_HTTP_URL": "http://127.0.0.1:11434/v1/embeddings",
    "ZVEC_MCP_HTTP_MODEL": "nomic-embed-text",
    "ZVEC_MCP_HTTP_DIM": "768"
  }
}
```

> **Important:** The `ZVEC_MCP_HTTP_DIM` value must match the output dimension of your chosen model. Common values: `1024` for Qwen3 0.6B embeddings, `768` for nomic-embed-text, and `384` for all-MiniLM-L6-v2.

### Local — sentence-transformers

Runs `all-MiniLM-L6-v2` entirely offline on your machine. 384 dimensions, uses MPS acceleration on Apple Silicon. No API key needed.

**Requires:** `pip install "zvec-mcp[local]"` (pulls in PyTorch)

```json
{
  "env": {
    "ZVEC_MCP_EMBEDDING": "local"
  }
}
```

The model is downloaded automatically on first use (~80 MB, cached in `~/.cache/torch/`).

### OpenAI

Uses the OpenAI Embeddings API. Requires a valid API key.

```json
{
  "env": {
    "ZVEC_MCP_EMBEDDING": "openai",
    "OPENAI_API_KEY": "sk-..."
  }
}
```

You can customize the model and dimension:

```json
{
  "env": {
    "ZVEC_MCP_EMBEDDING": "openai",
    "OPENAI_API_KEY": "sk-...",
    "ZVEC_MCP_OPENAI_MODEL": "text-embedding-3-large",
    "ZVEC_MCP_OPENAI_DIM": "3072"
  }
}
```

---

## Configuration reference

All settings are driven by environment variables, passed through the `env` block in your MCP config.

| Variable | Default | Description |
|----------|---------|-------------|
| `ZVEC_MCP_DATA_DIR` | `~/.zvec-mcp` | Root directory for vector database collections |
| `ZVEC_MCP_EMBEDDING` | `local` | Embedding backend: `local`, `openai`, or `http` |
| `ZVEC_MCP_CHUNK_SIZE` | `512` | Characters per chunk for knowledge ingestion |
| `ZVEC_MCP_CHUNK_OVERLAP` | `64` | Overlap between consecutive chunks |
| **HTTP backend** | | |
| `ZVEC_MCP_HTTP_URL` | `http://127.0.0.1:1234/v1/embeddings` | OpenAI-compatible embedding endpoint |
| `ZVEC_MCP_HTTP_MODEL` | `text-embedding-qwen3-embedding-0.6b` | Model name sent to the endpoint |
| `ZVEC_MCP_HTTP_API_KEY` | — | Bearer token (optional, depends on your server) |
| `ZVEC_MCP_HTTP_DIM` | `1024` | Embedding dimension (must match your model) |
| **OpenAI backend** | | |
| `OPENAI_API_KEY` | — | Required when using OpenAI backend |
| `ZVEC_MCP_OPENAI_MODEL` | `text-embedding-3-small` | OpenAI model name |
| `ZVEC_MCP_OPENAI_DIM` | `1536` | Embedding dimension |

---

## Tools reference

### Knowledge base (RAG)

| Tool | Description |
|------|-------------|
| `knowledge_ingest` | Chunk, embed, and store text for later retrieval. Accepts `text` and an optional `source` label. |
| `knowledge_ingest_file` | Read a file from disk and ingest its contents. Accepts a file `path`. |
| `knowledge_ingest_path` | Walk a directory, ingest matching markdown files, and rebuild the navigation sidecar. |
| `knowledge_search` | Semantic search over ingested documents. Accepts a `query` and optional `topk` (default 5). |
| `knowledge_navigate_file` | Read a markdown file and return outgoing wikilinks plus backlinks. |
| `knowledge_wikilink_retrieve` | Resolve a wikilink from a source file and return the target markdown content. |
| `knowledge_backlinks` | Return files that reference a markdown source file. |
| `knowledge_delete_source` | Remove all chunks from a given `source`. |
| `knowledge_stats` | Return collection statistics (doc count, embedding dimension, path). |

### Memory

| Tool | Description |
|------|-------------|
| `memory_remember` | Store a fact, preference, or observation. Accepts `text` and optional `category` (default `"general"`). |
| `memory_recall` | Semantic recall by query. Accepts `query`, optional `topk` (default 5), optional `category` filter. |
| `memory_forget` | Delete a specific memory by its `memory_id`. |
| `memory_forget_category` | Delete all memories in a `category`. |
| `memory_stats` | Return memory store statistics. |

### Status

| Tool | Description |
|------|-------------|
| `zvec_status` | Return server config, embedding backend, and stats for both collections. |

---

## Usage examples

Once registered, you can use the tools naturally in conversation with Claude Code:

**Ingest documentation for RAG:**

> "Ingest the contents of `docs/api-reference.md` into the knowledge base."

Claude will call `knowledge_ingest_file` with that path. You can then ask questions like:

> "How does the authentication flow work?"

Claude will call `knowledge_search` to retrieve relevant chunks and use them in its answer.

**Ingest an existing Obsidian wiki:**

> "Ingest `/Users/albert/projects/alber70g/notes/wiki` with `**/*.md`."

Claude will call `knowledge_ingest_path`. After search finds a relevant chunk,
Claude can call `knowledge_navigate_file` on the result source to inspect
wikilinks and backlinks, or `knowledge_wikilink_retrieve` to open a linked
document.

Example MCP tool arguments:

```json
{
  "root": "/Users/albert/projects/alber70g/notes/wiki",
  "glob_pattern": "**/*.md"
}
```

**Store project context as memory:**

> "Remember that this project uses PostgreSQL 16 and the primary database is called `appdb`."

Claude will call `memory_remember` with category `"project"`. Later, in any conversation:

> "What database does this project use?"

Claude will call `memory_recall` and retrieve the stored fact.

**Organize memories by category:**

Categories help you organize different types of information:

- `"preference"` — coding style, tool choices, naming conventions
- `"project"` — architecture decisions, database schemas, API contracts
- `"person"` — team member roles, contact info
- `"decision"` — past decisions with rationale

> "Remember that we decided to use JWT for auth instead of sessions — the main reason was stateless scaling."

Claude stores this with the `"decision"` category.

**Clean up:**

> "Delete all knowledge from source `docs/old-api.md`."
>
> "Forget all memories in the `project` category."

---

## Docker

The container runs `zvec-mcp` over stdio. MCP clients should start it with
`docker run -i` so JSON-RPC can flow over standard input and output.

Build the image:

```bash
docker build -t zvec-mcp:local .
```

Run it with persistent zvec data and the notes wiki mounted read-only:

```bash
docker run --rm -i \
  -e ZVEC_MCP_DATA_DIR=/data \
  -e ZVEC_MCP_EMBEDDING=http \
  -e ZVEC_MCP_HTTP_URL=http://host.docker.internal:1234/v1/embeddings \
  -e ZVEC_MCP_HTTP_MODEL=text-embedding-qwen3-embedding-0.6b \
  -e ZVEC_MCP_HTTP_DIM=1024 \
  -v zvec-mcp-data:/data \
  -v /Users/albert/projects/alber70g/notes/wiki:/wiki:ro \
  zvec-mcp:local
```

Example MCP client command:

```json
{
  "command": "docker",
  "args": [
    "run",
    "--rm",
    "-i",
    "-e",
    "ZVEC_MCP_DATA_DIR=/data",
    "-e",
    "ZVEC_MCP_EMBEDDING=http",
    "-e",
    "ZVEC_MCP_HTTP_URL=http://host.docker.internal:1234/v1/embeddings",
    "-e",
    "ZVEC_MCP_HTTP_MODEL=text-embedding-qwen3-embedding-0.6b",
    "-e",
    "ZVEC_MCP_HTTP_DIM=1024",
    "-v",
    "zvec-mcp-data:/data",
    "-v",
    "/Users/albert/projects/alber70g/notes/wiki:/wiki:ro",
    "zvec-mcp:local"
  ]
}
```

Inside Docker, use `/wiki` as the ingestion root:

```json
{
  "root": "/wiki",
  "glob_pattern": "**/*.md"
}
```

`host.docker.internal` is used so the container can reach LM Studio running on
the host machine. The Docker image installs only the core package and is
configured for HTTP embeddings, so it does not pull in PyTorch unless you build
a custom image with the `local` extra.

---

## Architecture

```
┌─────────────┐    stdio/JSON-RPC    ┌──────────────────────────┐
│ Claude Code  │◄───────────────────►│  zvec-mcp (FastMCP)      │
│   (client)   │                     │                          │
└─────────────┘                     │  ┌──────────┐            │
                                     │  │ knowledge │ chunk →   │
                                     │  │ manager   │ embed →   │
                                     │  │           │ store     │
                                     │  └─────┬────┘            │
                                     │        │                 │
                                     │  ┌─────▼────┐            │
                                     │  │   zvec    │ vector    │
                                     │  │collection │ search    │
                                     │  └─────┬────┘            │
                                     │        │                 │
                                     │  ┌─────▼────┐            │
                                     │  │  memory   │ remember  │
                                     │  │  manager  │ recall    │
                                     │  └──────────┘            │
                                     │                          │
                                     │  ┌──────────┐            │
                                     │  │embeddings│ local /   │
                                     │  │ (lazy)   │ openai /  │
                                     │  │          │ http      │
                                     │  └──────────┘            │
                                     └──────────────────────────┘
```

### Source layout

```
src/zvec_mcp/
├── server.py       # FastMCP server — tools registered via @mcp.tool()
├── config.py       # Env-driven dataclass, reads all ZVEC_MCP_* variables
├── embeddings.py   # Lazy-loaded embedding singleton (local, OpenAI, or HTTP)
├── knowledge.py    # RAG pipeline: chunk → embed → upsert → query
├── wiki.py         # Obsidian wikilink navigation helpers
└── memory.py       # Semantic memory: remember → recall → forget
```

### How RAG ingestion works

1. Text is split into overlapping chunks at sentence boundaries (configurable size and overlap)
2. Each chunk is embedded via the configured backend
3. Chunks are stored in a zvec `Collection` with fields: `source`, `chunk_idx`, `text`, `created_at`
4. Chunk IDs are content-addressed (`sha256(source:idx)`) — re-ingesting the same source updates in place

### How memory works

1. Each fact/observation is embedded and stored with a category tag
2. Memory IDs are content-addressed (`sha256(text)`) — storing the same text twice is a no-op (deduplication)
3. Recall uses cosine similarity with optional category filtering
4. Categories let you organize memories (e.g. `preference`, `project`, `person`, `decision`)

---

## Data storage

All data lives under `ZVEC_MCP_DATA_DIR` (default `~/.zvec-mcp/`):

```
~/.zvec-mcp/
├── knowledge/              # zvec collection for RAG chunks
├── memory/                 # zvec collection for memories
└── navigation_index.json   # sidecar wikilink/backlink index
```

Collections are created automatically on first use. To reset everything, delete the directory:

```bash
rm -rf ~/.zvec-mcp
```

---

## Troubleshooting

### Server not showing as connected

```bash
# Check MCP registration
claude mcp list

# Test the server directly (should print JSON-RPC on stdout)
zvec-mcp
# Or from source:
/path/to/zvec-mcp/.venv/bin/zvec-mcp
```

If the command is not found, make sure the installation directory is on your `PATH`, or use the full path in your MCP config.

### HTTP embedding errors

- **Connection refused:** Make sure your LM Studio / Ollama / vLLM server is running
- **401 Unauthorized:** Set `ZVEC_MCP_HTTP_API_KEY` to your server's API key
- **Dimension mismatch:** If you get errors when searching after changing models, delete your data directory (`rm -rf ~/.zvec-mcp`) and re-ingest — you cannot mix embeddings of different dimensions in the same collection

### Local embedding slow on first run

The `all-MiniLM-L6-v2` model (~80 MB) is downloaded on first use. Subsequent runs load from cache (`~/.cache/torch/`).

### `sentence-transformers` not found

The local backend requires the `local` extra. Install it:

```bash
pip install "zvec-mcp[local]"
```

Or switch to the `http` backend if you have LM Studio or Ollama running.

### Resetting the database

To start fresh, delete the data directory:

```bash
rm -rf ~/.zvec-mcp
```

Collections are recreated automatically on next use.

---

## Building the .mcpb bundle

To build the desktop extension from source:

```bash
# Install mcpb CLI
npm install -g @anthropic-ai/mcpb

# Install bundled dependencies (core only, no torch/sentence-transformers)
# IMPORTANT: let pip resolve versions — do NOT use --no-deps
pip install --target bundle/server/lib "mcp[cli]>=1.0.0" zvec numpy

# Copy zvec_mcp source into the bundle
cp -r src/zvec_mcp bundle/server/lib/zvec_mcp

# Strip caches (keep .dist-info — needed for importlib.metadata)
cd bundle/server/lib
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
cd ../../..

# Validate manifest and pack
mcpb validate bundle/manifest.json
mcpb pack bundle/ zvec-mcp-0.1.0.mcpb
```

> **Do not** strip `.dist-info` directories — the MCP SDK uses `importlib.metadata.version("mcp")` at import time and will fail without them.
> **Do not** use `--no-deps` — pydantic and pydantic-core have strict version coupling and must be resolved together.

---

## Dependencies

| Package | Role |
|---------|------|
| [zvec](https://github.com/alibaba/zvec) | Vector database engine |
| [mcp](https://pypi.org/project/mcp/) | Model Context Protocol SDK (FastMCP) |
| [sentence-transformers](https://www.sbert.net/) | Local embeddings (optional) |
| [openai](https://pypi.org/project/openai/) | OpenAI embeddings (optional) |

## License

Apache-2.0
