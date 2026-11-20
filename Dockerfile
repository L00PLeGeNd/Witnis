# Stdio MCP image. Glama Admin → Dockerfile still has to be filled
# (build steps + CMD); this file is the local/reference image.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir . \
 && mkdir -p /data /app/.witnis

ENV WITNIS_DB=/data/index.sqlite
VOLUME ["/data"]

ENTRYPOINT ["witnis", "mcp"]
