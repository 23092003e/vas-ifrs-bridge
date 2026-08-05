#!/usr/bin/env bash
# Wrapper script to execute the batch embedding ingestion pipeline.

set -euo pipefail

SCOPE="shared"
TENANT_ID=""
RECREATE=false
DRY_RUN=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --scope|--tenant-id)
            if [[ "$#" -lt 2 || -z "$2" ]]; then
                echo "Missing value for $1" >&2
                exit 1
            fi
            if [[ "$1" == "--scope" ]]; then
                SCOPE="$2"
            else
                TENANT_ID="$2"
            fi
            shift 2
            ;;
        --recreate)
            RECREATE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--scope vas|ifrs|tenant|shared|all] [--tenant-id UUID] [--recreate] [--dry-run]"
            exit 0
            ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
done

case "$SCOPE" in
    vas|ifrs|tenant|shared|all) ;;
    *)
        echo "Unknown scope: $SCOPE. Allowed: vas | ifrs | tenant | shared | all" >&2
        exit 1
        ;;
esac

if [[ "$SCOPE" == "tenant" || "$SCOPE" == "all" ]]; then
    UUID_PATTERN='^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    if [[ ! "$TENANT_ID" =~ $UUID_PATTERN ]]; then
        echo "--tenant-id must be a valid UUID for scope '$SCOPE'" >&2
        exit 1
    fi
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"

echo "=========================================================="
echo " Starting Ingestion Pipeline for Scope: $SCOPE"
echo "=========================================================="

if [[ -n "${INGEST_PYTHON:-}" ]]; then
    PYTHON_BIN="$INGEST_PYTHON"
elif [[ -x "$PROJECT_ROOT/apps/backend/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/apps/backend/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "Python not found. Create apps/backend/.venv or set INGEST_PYTHON." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/apps/backend:$PROJECT_ROOT/ingestion${PYTHONPATH:+:$PYTHONPATH}"

EXTRA_ARGS=()
if [[ "$RECREATE" == true ]]; then
    EXTRA_ARGS+=(--recreate)
fi
if [[ "$DRY_RUN" == true ]]; then
    EXTRA_ARGS+=(--dry-run)
fi

ingest_collection() {
    local docs_dir="$1"
    local collection="$2"
    local scope="$3"
    local tenant_id="${4:-}"

    if [ ! -d "$docs_dir" ]; then
        echo "[SKIP] Directory not found: $docs_dir"
        return
    fi

    # Count matching files
    local file_count
    file_count=$(find "$docs_dir" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.xlsx" -o -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$file_count" -eq 0 ]; then
        echo "[SKIP] No documents found in $docs_dir"
        return
    fi

    echo ""
    echo "==> Ingesting $file_count docs from $docs_dir to collection '$collection'"
    
    local command=(
        "$PYTHON_BIN"
        ingestion/pipelines/embedders/batch_embed.py
        --docs "$docs_dir"
        --collection "$collection"
        --scope "$scope"
    )
    if [[ -n "$tenant_id" ]]; then
        command+=(--tenant-id "$tenant_id")
    fi
    command+=("${EXTRA_ARGS[@]}")

    printf 'Running:'
    printf ' %q' "${command[@]}"
    printf '\n'
    "${command[@]}"
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
esac

echo "=========================================================="
echo " Ingestion Pipeline Completed."
echo "=========================================================="
