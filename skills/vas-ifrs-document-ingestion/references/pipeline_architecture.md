# Document Ingestion Pipeline Architecture

The document ingestion pipeline processes heavily structured legal and regulatory texts (Vietnamese Accounting Standards and IFRS) and inserts them into the Qdrant Vector Database.

## Pipeline Components

1.  **Parsing Engine**:
    -   `unstructured_runner.py` uses libraries like PyMuPDF (PDFs), python-docx (DOCX), and openpyxl (XLSX).
    -   It cleans and normalizes metadata and text before passing it to the chunker.
2.  **Section-Aware Chunker** (`app/rag/chunker.py`):
    -   Uses markdown heading splitters to keep logically related sections together.
    -   Target chunk size is 800 tokens with a 120-token overlap.
    -   Tables are preserved intact up to 1500 tokens.
3.  **Multilingual Vector Embedding** (`app/rag/embedder.py`):
    -   **Primary Model**: BAAI/bge-m3 hosted via Text-Embeddings-Inference (TEI). Produces 1024-dimension dense vectors and sparse semantic representations.
    -   **Fallback Model**: Google Gemini `text-embedding-004` (768-dimension dense vector). Used automatically if the local TEI server is offline.
4.  **Vector Storage Segregation**:
    -   Data is separated into isolated Qdrant collections: `kb_shared_vas` (Circulars, Decisions), `kb_shared_ifrs` (Core IFRS/IAS Standards), and `tenant_<id>` (Private Corporate Policies).
