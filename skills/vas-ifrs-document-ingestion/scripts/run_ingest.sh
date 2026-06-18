#!/usr/bin/env bash
# Wrapper script to execute the batch embedding ingestion pipeline.

set -e

SCOPE="shared"
TENANT_ID="dev-tenant"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --scope) SCOPE="$2"; shift ;;
        --tenant-id) TENANT_ID="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

PROJECT_ROOT="/Users/manh-greydigi/vas-ifrs-bridge"

echo "=========================================================="
echo " Starting Ingestion Pipeline for Scope: $SCOPE"
echo "=========================================================="

# Activate the python virtual environment
if [ -f "$PROJECT_ROOT/apps/backend/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/apps/backend/.venv/bin/activate"
else
    echo "Warning: Python virtual environment not found at $PROJECT_ROOT/apps/backend/.venv"
    echo "Attempting to run with system python..."
fi

# Run the python script
cd "$PROJECT_ROOT"

ingest_collection() {
    local docs_dir="$1"
    local collection="$2"
    local scope="$3"
    local tenant_id="$4"

    if [ ! -d "$docs_dir" ]; then
        echo "[SKIP] Directory not found: $docs_dir"
        return
    fi

    # Count matching files
    local file_count=$(find "$docs_dir" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.xlsx" -o -name "*.xls" -o -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$file_count" -eq 0 ]; then
        echo "[SKIP] No documents found in $docs_dir"
        return
    fi

    echo ""
    echo "==> Ingesting $file_count docs from $docs_dir to collection '$collection'"
    
    local cmd="PYTHONPATH=apps/backend:ingestion python ingestion/pipelines/embedders/batch_embed.py --docs \"$docs_dir\" --collection \"$collection\" --scope \"$scope\""
    if [ -n "$tenant_id" ]; then
        cmd="$cmd --tenant-id \"$tenant_id\""
    fi
    
    echo "Running: $cmd"
    eval "$cmd"
}

RAW_DIR="ingestion/raw"

case "$SCOPE" in
    vas)
        ingest_collection "$RAW_DIR/shared/vas" "kb_shared_vas" "shared"
        ;;
    ifrs)
        ingest_collection "$RAW_DIR/shared/ifrs" "kb_shared_ifrs" "shared"
        ;;
    tenant)
        ingest_collection "$RAW_DIR/tenant/$TENANT_ID" "tenant_$TENANT_ID" "tenant" "$TENANT_ID"
        ;;
    shared)
        ingest_collection "$RAW_DIR/shared/vas" "kb_shared_vas" "shared"
        ingest_collection "$RAW_DIR/shared/ifrs" "kb_shared_ifrs" "shared"
        ;;
    all)
        ingest_collection "$RAW_DIR/shared/vas" "kb_shared_vas" "shared"
        ingest_collection "$RAW_DIR/shared/ifrs" "kb_shared_ifrs" "shared"
        ingest_collection "$RAW_DIR/tenant/$TENANT_ID" "tenant_$TENANT_ID" "tenant" "$TENANT_ID"
        ;;
    *)
        echo "Unknown scope: $SCOPE. Allowed: vas | ifrs | tenant | shared | all"
        exit 1
        ;;
esac

echo "=========================================================="
echo " Ingestion Pipeline Completed."
echo "=========================================================="
