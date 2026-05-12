FROM python:3.11-slim AS base
WORKDIR /app
RUN pip install uv

FROM base AS deps
COPY pyproject.toml .
RUN uv pip install --system -e .

FROM deps AS runner
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
