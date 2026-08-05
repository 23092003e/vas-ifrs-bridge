FROM python:3.11-slim AS base
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser && chown appuser:appuser /app
RUN pip install --no-cache-dir uv==0.11.15

FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv export --quiet --frozen --no-dev --no-emit-project --no-header \
      --output-file /tmp/requirements.txt \
    && uv pip install --system --require-hashes --requirements /tmp/requirements.txt

FROM deps AS runner
COPY --chown=appuser:appuser . .
RUN uv pip install --system --no-deps --editable .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
