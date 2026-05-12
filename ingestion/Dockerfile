FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY . .
RUN uv pip install --system unstructured pymupdf httpx qdrant-client
CMD ["python", "batch_embed.py"]
