FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ZVEC_MCP_DATA_DIR=/data \
    ZVEC_MCP_EMBEDDING=http \
    ZVEC_MCP_HTTP_URL=http://host.docker.internal:1234/v1/embeddings \
    ZVEC_MCP_HTTP_MODEL=text-embedding-qwen3-embedding-0.6b \
    ZVEC_MCP_HTTP_DIM=1024

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN mkdir -p /data /wiki

VOLUME ["/data", "/wiki"]

ENTRYPOINT ["zvec-mcp"]

