---
name: rag-evaluation-runner
description: "Executes retrieval and hallucination evaluation scripts for the RAG pipeline."
---

# RAG Evaluation Runner Skill

Use this skill when you need to evaluate the accuracy, recall, and hallucination rate of the RAG pipeline. This is critical for ensuring that the LLM is providing verifiable, audit-ready information without making up numbers or laws.

## Trigger Scenarios
- "Run the nightly evaluation metrics on the RAG pipeline."
- "What is the Recall@10 score for the VAS QA dataset?"
- "We updated the chunking strategy, can you check if the hallucination metrics improved?"

## Workflow

1.  **Locate the Datasets:** Evaluation datasets (JSONL format) are located in `apps/backend/app/eval/datasets/`.
    -   Retrieval dataset: `vas_qa_vi.jsonl`
    -   Hallucination dataset: `hallucination_test.jsonl`
2.  **Verify Environment:** Ensure that the backend is running and the Python environment has the `pytest` and eval-related dependencies installed (`uv pip install -e ".[dev]"`).
3.  **Run Evaluations:** Use the provided script `scripts/run_nightly_evals.sh` to execute both retrieval and hallucination evaluations.
    -   Example: `./scripts/run_nightly_evals.sh`
4.  **Target Metrics:** Ensure the output meets our enterprise standards:
    -   **Recall@10** must be $\ge 0.85$.
    -   **Faithfulness** must be $\ge 0.85$.
5.  **Report Results:** Extract the key metrics from the console output and report them to the user.
