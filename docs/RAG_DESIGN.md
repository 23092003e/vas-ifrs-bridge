# RAG design — current implementation

## Ingestion

Supported input formats are PDF, DOCX, XLSX, HTML, Markdown, and plain text. Parsers produce normalized text and metadata; the chunker targets 800 tokens with 120-token overlap and preserves section context.

`app/rag/embedder.py` and the standalone batch ingestion pipeline use Ollama `bge-m3`. The vector size is fixed at 1024. There is no cross-model embedding fallback because mixing dimensions or embedding spaces in one collection would make retrieval invalid.

```text
document -> parser -> normalizer -> chunker -> Ollama bge-m3 -> Qdrant
```

Each Qdrant payload carries identifiers and retrieval filters such as document/chunk ID, source URI, language, scope, tenant ID, standard code, section path, and text.

## Query pipeline

```text
query
  -> bge-m3 query embedding
  -> dense top 40 + sparse top 40
  -> score fusion
  -> optional TEI cross-encoder rerank
  -> top 8 chunks
  -> citation-wrapped context
  -> LLM streaming
  -> citation validation
```

The retriever searches the collections allowed by request scope:

- `shared`: `kb_shared_vas` and/or `kb_shared_ifrs`
- `tenant`: `tenant_<tenant_id>`
- `both`: shared plus that tenant's private collection

TEI is used only for cross-encoder reranking. If `TEI_URL` is absent or the service is unavailable, the reranker returns candidates ordered by their existing dense/fused scores. Embedding still requires Ollama and fails explicitly if it is unavailable.

## Citation contract

Retrieved chunks are numbered and wrapped before prompt composition. The model references them as `[Cn]`. The validator rejects or corrects references that are not present in the supplied citation map and strips unresolved citation markers if correction does not resolve them.

Citation validation checks provenance syntax and source membership. It does not independently prove the legal or accounting correctness of an answer; human review remains required for material decisions.

## LLM routing

The request `reasoning` field selects a configured provider tier. Local development can use Ollama without external API keys. External provider keys are optional and only needed when their corresponding tier/evaluator is enabled.

## Evaluation

Retrieval and hallucination evaluation runners live in `apps/backend/app/eval/`. Datasets are intentionally external/versioned inputs rather than committed legal corpora. The nightly workflow requires:

- `RETRIEVAL_EVAL_DATASET_URL`
- `HALLUCINATION_EVAL_DATASET_URL`
- `EVAL_QDRANT_URL`
- `EVAL_OLLAMA_BASE_URL`
- `GEMINI_API_KEY` for the hallucination judge

The workflow uploads JSON results as GitHub Actions artifacts.

## Failure behavior

| Failure | Behavior |
|---|---|
| Ollama embedding unavailable | Explicit request/ingestion failure; no incompatible fallback |
| Qdrant unavailable | Retrieval/readiness failure |
| TEI unavailable | Degraded reranking using existing scores |
| No relevant chunks | Agent answers under its no-context prompt rules |
| Invalid citation keys | One correction attempt, then unresolved markers removed |
| LLM provider failure | Error event on the SSE stream |

## Tunable constants

| Setting | Value |
|---|---:|
| Dense candidates | 40 |
| Sparse candidates | 40 |
| Final reranked chunks | 8 |
| Embedding dimension | 1024 |
| Chunk target | 800 tokens |
| Chunk overlap | 120 tokens |

Changing the embedding model or dimension requires creating and rebuilding compatible Qdrant collections; never silently reuse existing vectors.
