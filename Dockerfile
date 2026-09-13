# The hosted server at https://mcp.ceorater.com/mcp. One image, built by Cloud
# Build on every push to main (.github/workflows/deploy.yml), run on Cloud Run.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_TRANSPORT=http \
    PORT=8080

WORKDIR /app

# Dependencies first, so a source-only change reuses the cached layer.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY pyproject.toml README.md LICENSE ./
COPY ceorater_mcp ./ceorater_mcp
RUN pip install --no-deps .

RUN useradd --system --no-create-home mcp
USER mcp

EXPOSE 8080
CMD ["ceorater-mcp"]
