FROM python:3.11-slim AS base
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser && chown appuser:appuser /app
RUN pip install uv

FROM base AS deps
COPY pyproject.toml .
RUN uv pip install --system -e .

FROM deps AS runner
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
