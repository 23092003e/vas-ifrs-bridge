#!/usr/bin/env bash
# Script to run RAG retrieval and hallucination evaluations.

set -e

PROJECT_ROOT="/Users/manh-greydigi/vas-ifrs-bridge"
DATASET_DIR="app/eval/datasets"

echo "=========================================================="
echo " Starting Nightly RAG Evaluations"
echo "=========================================================="

# Activate the python virtual environment
if [ -f "$PROJECT_ROOT/apps/backend/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/apps/backend/.venv/bin/activate"
else
    echo "Error: Python virtual environment not found at $PROJECT_ROOT/apps/backend/.venv"
    echo "Please set up the backend environment first."
    exit 1
fi

cd "$PROJECT_ROOT/apps/backend"

echo ""
echo "--- Running Retrieval Evaluations (Recall@K) ---"
python -m app.eval.retrieval_eval --dataset "$DATASET_DIR/vas_qa_vi.jsonl" --k 10

echo ""
echo "--- Running Hallucination Evaluations ---"
python -m app.eval.hallucination_eval --dataset "$DATASET_DIR/hallucination_test.jsonl"

echo ""
echo "=========================================================="
echo " Evaluations Completed."
echo "=========================================================="
