# Double Entry Validation Rules (VAS vs IFRS)

When generating adjustment entries between VAS and IFRS, agents must adhere to the fundamental accounting equation and specific reporting standards.

## Rule 1: The Balance Guard
Every journal entry payload MUST balance.
$$\sum \text{Debits} - \sum \text{Credits} = 0$$

If the math does not sum perfectly to 0, the backend `UnbalancedJE` exception will reject the payload before it enters the database.

## Common Adjustment Patterns

### 1. Operating Leases (VAS 15 to IFRS 16)
Under VAS, operating leases are expensed on a straight-line basis. Under IFRS 16, they must be capitalized as a Right-of-Use (ROU) Asset and a Lease Liability.

**Required Adjustment:**
-   `Debit`: ROU Asset (Capitalization of present value of lease payments)
-   `Credit`: Lease Liability
-   *Follow-up Entry (Depreciation)*:
    -   `Debit`: Depreciation Expense
    -   `Credit`: Accumulated Depreciation - ROU Asset
-   *Follow-up Entry (Interest)*:
    -   `Debit`: Interest Expense
    -   `Credit`: Lease Liability

### 2. Expected Credit Losses (VAS vs IFRS 9)
VAS typically provisions for bad debts based on historical aging. IFRS 9 requires a forward-looking Expected Credit Loss (ECL) model.

**Required Adjustment:**
-   `Debit`: Credit Loss Expense (P&L)
-   `Credit`: Allowance for Expected Credit Losses (Balance Sheet)
*Note: The adjustment amount is the difference between the VAS provision and the IFRS 9 calculated ECL.*

## Troubleshooting the Prompt
If the `AdjustmentAgent` is repeatedly failing the math check, review `prompts/registry.yaml` and ensure the system prompt strictly emphasizes: "You MUST generate both a debit and credit side for the entry, and the absolute values MUST match perfectly."
