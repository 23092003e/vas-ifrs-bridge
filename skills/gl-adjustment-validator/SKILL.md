---
name: gl-adjustment-validator
description: "Validates double-entry accounting constraints (Debit = Credit) for the GL Mapping and Adjustment Agents."
---

# GL Adjustment Validator Skill

Use this skill when you are modifying or debugging the `GLMappingAgent`, `AdjustmentAgent`, or general ledger logic. This ensures that any generated journal entries maintain the fundamental mathematical equation of accounting.

## Trigger Scenarios
- "The journal entry failed with an UnbalancedJE exception."
- "Debug the IFRS 16 lease liability adjustment."
- "Review the prompt for the Adjustment Agent to make sure it respects the Debit/Credit rules."

## Workflow

1.  **Analyze the Mappings:** Review the GL mapping output from the frontend payload or the `GLMappingAgent`. Identify the `src_account_code` and `target_account_code`.
2.  **Verify Adjustment Payload:** An adjustment payload usually looks like:
    ```json
    {
      "debit_account": "IFRS Right-of-Use Asset",
      "credit_account": "IFRS Lease Liability",
      "amount": 150000.0
    }
    ```
3.  **Run Math Checks:** Manually verify or write a short script to ensure that `sum(debits) == sum(credits)` for every entry proposed by the LLM.
4.  **Enforce System Rules:** The backend has a mathematical balance guard. If an agent's prompt leads to an unbalanced entry, you must update the prompt template in `prompts/registry.yaml` to instruct the LLM to balance its output correctly.
5.  **Run Tests:** Execute `pytest tests/unit/ -k "test_balance_guard"` to confirm that the strict constraints are enforced.

## Reference Material
For a quick refresher on common VAS vs IFRS double-entry mappings (like IFRS 16 and IFRS 9), see [Double Entry Rules](file:///Users/manh-greydigi/vas-ifrs-bridge/skills/gl-adjustment-validator/references/double_entry_rules.md).
