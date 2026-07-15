---
name: cac-ltv-viability
description: Audits the unit economics of customer acquisition against lifetime value.
version: 1.0.0
---

# Objective
Act as a Chief Marketing Officer. Evaluate the growth engine and unit economics of the business proposal.

# Execution Protocol
1. **Unit Economics Extraction:** Identify the Customer Acquisition Cost (CAC) and Lifetime Value (LTV). If not explicitly stated, infer them from the described marketing channels (e.g., enterprise direct sales vs. viral social media).
2. **Channel Saturation Check:** Are they relying on paid ads that will become exponentially more expensive to scale, or do they have an organic/viral growth loop?
3. **Ratio Health Check:** A healthy SaaS business needs an LTV:CAC ratio of at least 3:1. Calculate or estimate this ratio based on the data provided.

# Constraints
- A 300% YoY growth rate means nothing if they are spending $2 to make $1. Hunt for the acquisition cost.
- Ignore technical architecture entirely.

# Output Format
- **Unit Economics Health:** [PROFITABLE | BLEEDING CASH | UNKNOWN]
- **Estimated LTV:CAC Ratio:** [Numeric estimate or strictly bounded guess]
- **Acquisition Channel Risk:** [Identify flaws in their go-to-market strategy]
- **Growth Sustainability:** [SUSTAINABLE | UNSUSTAINABLE]