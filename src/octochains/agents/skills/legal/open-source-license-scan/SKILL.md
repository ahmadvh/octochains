---
name: open-source-license-scan
description: Scans technology stacks and dependencies for viral open-source licensing contamination (Copyleft risks).
version: 1.0.0
---

# Objective
Analyze the provided software architecture, tech stack, or dependencies to identify severe Intellectual Property (IP) and licensing liabilities for a commercial/proprietary enterprise product.

# Execution Protocol
1. **Viral License Detection:** Scan the text for mentions of strictly copyleft licenses (e.g., GNU GPL, AGPL). 
2. **SaaS Contamination (AGPL):** If the system operates as a cloud service (SaaS) and utilizes AGPL components (like early MongoDB or modern open-source vector databases), flag this as a FATAL LIABILITY, as it legally requires open-sourcing the entire proprietary backend.
3. **Permissive Validation:** Identify safely usable permissive licenses (MIT, Apache 2.0, BSD) and mark them as cleared.

# Constraints
- Focus strictly on software licensing. Ignore data privacy or operational security.
- Do not provide legal advice; provide a factual license compatibility map.

# Output Format
- **IP Contamination Risk:** [CRITICAL | SAFE]
- **Flagged Dependencies:** [List tech stack components with GPL/AGPL risks]
- **Safe Dependencies:** [List cleared MIT/Apache components]