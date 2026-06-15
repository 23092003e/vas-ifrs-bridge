#!/usr/bin/env bash
# Wrapper script to execute the batch embedding ingestion pipeline.

set -e

SCOPE="shared"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --scope) SCOPE="$2"; shift ;;
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
python ingestion/batch_embed.py --scope "$SCOPE"

echo "=========================================================="
echo " Ingestion Pipeline Completed."
echo "=========================================================="
