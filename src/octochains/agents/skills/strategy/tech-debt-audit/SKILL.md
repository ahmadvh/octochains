---
name: tech-debt-audit
description: Audits architectural choices for hidden scalability bottlenecks and operational tech debt.
version: 1.0.0
---

# Objective
Evaluate the underlying technology stack, infrastructure choices, and engineering operations. Ignore revenue or marketing strategy.

# Execution Protocol
1. **Scalability Bottlenecks:** Identify components of the architecture that will fundamentally break or incur exponential costs if user traffic 10x's overnight.
2. **Key-Person Risk:** Analyze the engineering team structure. If the architecture is highly complex and reliant on a single founder/architect, flag this as a critical operational risk.
3. **Refactor Timeline:** Estimate the technical cost and time required to migrate this stack into standard enterprise infrastructure.

# Constraints
- Do not evaluate UI/UX unless it directly impacts backend API load.
- Assume all "custom-built" core routing systems will require a full rewrite within 12 months.

# Output Format
- **Architecture Viability:** [SCALABLE | FRAGILE | REQUIRES REWRITE]
- **Estimated Refactor Timeline:** [e.g., 3-6 Months]
- **Critical Technical Blockers:** [List structural flaws]
- **Key-Person Dependency:** [Risk assessment of the engineering team]