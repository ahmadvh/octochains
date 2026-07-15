---
name: runway-burn-analysis
description: Extracts explicit financial metrics to mathematically evaluate cash runway and margin viability.
version: 1.0.0
---

# Objective
Evaluate the provided business dossier strictly from the perspective of financial survival and capital efficiency. Ignore product vision, marketing hype, or technical elegance.

# Execution Protocol
1. **Capital Mathematics:** Extract the Monthly Recurring Revenue (MRR), Annual Recurring Revenue (ARR), and Monthly Burn Rate. If any metric is missing, estimate a worst-case scenario based on stated headcount or infrastructure costs.
2. **Runway Calculation:** Calculate the exact runway timeline (in months) before the company reaches zero cash, assuming no new funding.
3. **Margin Risk Assessment:** Identify structural costs (e.g., cloud infrastructure, massive sales teams) that fundamentally threaten the profit margin.

# Constraints
- Be ruthlessly pessimistic. Assume growth projections are exaggerated by 50%.
- If a financial metric is mathematically impossible, explicitly call out the discrepancy as a "Valuation Illusion."

# Output Format
- **Financial Viability:** [STABLE | AT RISK | IMMINENT DANGER]
- **Runway Estimate:** [X Months]
- **Core Financial Discrepancies:** [List any mathematical impossibilities in the pitch]
- **Primary Margin Threat:** [The single biggest cost center]