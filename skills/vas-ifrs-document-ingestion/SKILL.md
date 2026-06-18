---
name: vas-ifrs-document-ingestion
description: "Ingests VAS circulars and IFRS standards into the Qdrant Vector Database."
---

# Document Ingestion Pipeline Skill

Use this skill when the user asks to add new legal documents (Vietnamese Accounting Standards - VAS Circulars or International Financial Reporting Standards - IFRS) into the knowledge base, or when there's an issue with vector embedding search and documents need to be re-indexed.

## Trigger Scenarios
- "We have a new VAS circular, please add it to the system."
- "Re-index the IFRS standards."
- "Why is the search not finding the latest tax decree? Can you ingest it?"

## Workflow

1.  **Locate the File:** Verify the file (PDF, DOCX, XLSX, or HTML) exists in the correct raw directory:
    -   VAS documents: `ingestion/raw/shared/vas/`
    -   IFRS documents: `ingestion/raw/shared/ifrs/`
    -   Tenant-specific documents: `ingestion/raw/tenant/<tenant_id>/`
2.  **Verify Environment:** Ensure that the Docker services (Qdrant, Redis) are running.
3.  **Run Ingestion:** Use the provided script `skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh` to trigger the Python offline embedding process. Provide the correct `--scope` parameter.
    -   Example: `./skills/vas-ifrs-document-ingestion/scripts/run_ingest.sh --scope shared`
4.  **Validate Completion:** Check the output logs for the number of chunks successfully embedded into `kb_shared_vas` or `kb_shared_ifrs`.
5.  **Fallback Awareness:** If the BAAI/bge-m3 TEI embedding server is offline, the system will automatically fall back to Gemini `text-embedding-004`. Note this in your report if it happens.

## Reference Architecture
For details on how the document pipeline splits headers, extracts tables, and creates overlapping chunks, read [Pipeline Architecture](file:///Users/manh-greydigi/vas-ifrs-bridge/skills/vas-ifrs-document-ingestion/references/pipeline_architecture.md).
